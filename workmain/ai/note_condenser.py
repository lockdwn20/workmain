"""
AI-powered condensation of meeting notes into one-line summaries for Clockify.

Takes multiple meeting notes and condenses them into a professional, concise summary
suitable for time tracking entries.
"""

from typing import List, Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session

from workmain.database.models import Meeting, Note
from workmain.ai.base_provider import GenerationRequest, ProviderType
from workmain.ai.cost_tracker import get_cost_tracker
from workmain.ai.provider_manager import get_provider_manager
from workmain.database.repositories.ai_costs_repo import AiCostRepository
from workmain.templates_engine import get_style_adapter


def _compute_condensed_tags(source_notes: List[Note]) -> List[str]:
    """Classify a condensed meeting summary's tags from its source notes'
    own tags (Item 69 Design Rule 8).

    Called with the same note set condense_meeting()'s own note-selection
    query already returns (info-only notes pre-filtered out by that query,
    not by this function). An empty source_notes list — the all-info-only
    case — falls through to the ['info-only'] branch below.
    """
    all_tags = set()
    for n in source_notes:
        all_tags |= set(n.tags or [])

    has_internal_only = 'internal-only' in all_tags
    has_client_report = 'client-report' in all_tags
    has_both = 'both' in all_tags
    is_client_facing = has_client_report or has_both

    if has_internal_only and is_client_facing:
        # Genuinely mixed-audience sources: conservative -- keep the whole
        # synthesized summary out of the client report rather than risk
        # blending internal-only content into client-visible output
        # (Ray, 20260728). Expected to be rare in practice.
        return ['internal-only']
    if is_client_facing:
        # No internal-only source present: honor the sources' own explicit
        # client-facing intent, including a pure 'both' source (fixes the
        # B1 classifier defect -- Opus review round 1 -- where a lone
        # 'both'-tagged source wrongly failed to vote on the internal axis).
        return ['both'] if has_both else ['client-report']
    if has_internal_only:
        return ['internal-only']
    # Empty (or, in principle, non-empty-but-no-routing-tag) source set.
    # Reached two ways in practice: (a) condense_meeting()'s own query
    # already filters info-only notes out before this function ever sees
    # them, so an all-info-only meeting produces an EMPTY notes list here
    # -- this is the set behind the "Attended <Meeting>" fallback; or (b)
    # a non-empty set where no note carries any report-routing tag (e.g.
    # a carry-forward-only note). Either way, ['info-only'] keeps the
    # result out of both reports.
    return ['info-only']


class NoteCondenser:
    """
    AI-powered note condensation for meetings.
    
    Condenses multiple meeting notes into a single professional summary
    suitable for Clockify time entry descriptions.
    
    Now includes writing style context to ensure summaries match
    the user's established voice and tone from reports.
    """
    
    def __init__(self, session: Session):
        """
        Initialize note condenser.
        
        Args:
            session: Database session for queries and updates
        """
        self.session = session
        self.cost_tracker = get_cost_tracker()
        self.style_adapter = get_style_adapter()
        self.provider_manager = get_provider_manager()
    
    def condense_meeting(
        self,
        meeting: Meeting,
        provider: Optional[ProviderType] = None
    ) -> Tuple[str, List[str]]:
        """
        Condense all notes from a meeting into a single summary.

        Args:
            meeting: Meeting object with notes to condense
            provider: AI provider to use (defaults to Claude)

        Returns:
            (condensed one-line summary, resolved tags for the summary note)

        Raises:
            ValueError: If meeting has no notes to condense
        """
        # Get meeting from database to ensure it's attached to our session
        db_meeting = self.session.query(Meeting).filter(
            Meeting.id == meeting.id
        ).first()
        
        if not db_meeting:
            raise ValueError(f"Meeting with ID {meeting.id} not found in database")
        
        # Get notes for this meeting occurrence only (scoped to meeting date),
        # excluding info-only (#ifo) notes and condensed summary notes.
        # Date scoping prevents notes from previous recurring occurrences that share
        # the same meeting_id from polluting the condensation input.
        meeting_date = db_meeting.start_time.date()
        notes = self.session.query(Note).filter(
            Note.meeting_id == db_meeting.id,
            Note.created_date == meeting_date,
            ~Note.tags.op('@>')(['info-only']),
            Note.source != 'condensed'
        ).order_by(Note.created_at).all()

        resolved_tags = _compute_condensed_tags(notes)

        if not notes:
            # All notes are info-only (#ifo), return default message
            default_summary = f"Attended {db_meeting.title}"
            db_meeting.condensed_summary = default_summary
            db_meeting.condensed_at = datetime.now()
            self.session.commit()
            return default_summary, resolved_tags
        
        # Build condensation prompt (now includes writing style)
        prompt = self._build_condensation_prompt(db_meeting, notes)
        
        # Generate condensed summary
        request = GenerationRequest(
            prompt=prompt,
            max_tokens=1024,  # Gemini 2.5 Flash thinking tokens count against this budget; 200 caused truncation
            temperature=0.3,  # Low temperature for consistency
            system_prompt=self._get_system_prompt()
        )
        
        # Track cost
        self.cost_tracker.start_report(f"condense_{db_meeting.title}", datetime.now().date())
        
        try:
            # Generate using config-driven provider ('note_condensation' entry in ai_settings.json)
            response, _ = self.provider_manager.generate(
                request,
                report_type='note_condensation',
                provider_override=provider if provider else None,
            )

            # Track cost
            self.cost_tracker.track_section(
                section_name="condensation",
                provider=response.provider.value,
                model=response.model,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                cost=response.cost
            )

            # Update meeting with condensed summary
            db_meeting.condensed_summary = response.content.strip()
            db_meeting.condensed_at = datetime.now()
            self.session.commit()

            # Persist ai_costs row
            AiCostRepository(self.session).create(
                interaction_type='condensation',
                provider=response.provider.value,
                model=response.model,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                cost_usd=response.cost,
                meeting_id=db_meeting.id,
                context_label=db_meeting.title,
            )

            return db_meeting.condensed_summary, resolved_tags

        finally:
            self.cost_tracker.end_report(0.0)  # No generation time tracking needed
    
    def _build_condensation_prompt(
        self,
        meeting: Meeting,
        notes: List[Note]
    ) -> str:
        """
        Build the prompt for AI condensation.
        
        Now includes writing style context for consistent voice.
        
        Args:
            meeting: Meeting object
            notes: List of Note objects from the meeting
            
        Returns:
            Formatted prompt string
        """
        # Format notes
        notes_text = "\n".join([
            f"- {note.content}"
            for note in notes
        ])
        
        # Build base prompt
        prompt = f"""Condense the following meeting notes into a single professional one-line summary suitable for a time tracking entry.

Meeting: {meeting.title}
Duration: {meeting.duration_hours:.1f} hours
Date: {meeting.start_time.strftime('%Y-%m-%d')}

Notes:
{notes_text}"""
        
        # Prepend writing style context via StyleAdapter
        style_context = self.style_adapter.get_style_prompt("internal")
        if style_context:
            prompt = f"WRITING STYLE CONTEXT:\n{style_context}\n\n{prompt}"

        # Add requirements
        prompt += """

Requirements:
1. Create ONE concise sentence (max 200 characters)
2. Use professional, action-oriented language
3. Include key topics, decisions, or blockers
4. Format: "<Meeting type>: <key points>"
5. Do NOT include tags, formatting, or metadata
6. Be specific and concrete
7. Match the established writing style and voice shown above"""
        
        # Add examples
        prompt += """

Example formats:
- "Team standup: Fixed authentication bug, discussed Q1 roadmap, blocked on API keys"
- "Client review: Presented dashboard mockups, received approval for phase 2, scheduled follow-up"
- "Sprint planning: Estimated 23 story points, assigned tasks, identified 2 blockers"

Condensed summary:"""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """
        Get system prompt for condensation.
        
        Returns:
            System prompt string
        """
        return """You are a professional assistant helping condense meeting notes into concise, 
professional summaries for time tracking systems. Your summaries should be:

- Concise (one sentence, max 200 characters)
- Action-oriented and specific
- Professional and clear
- Free of tags, formatting, or metadata
- Focused on outcomes, decisions, and key topics
- Consistent with the user's established writing style

Do not include pleasantries or unnecessary words. Be direct and informative."""
    
    def get_condensed_summary(self, meeting: Meeting) -> Optional[str]:
        """
        Get existing condensed summary for a meeting.
        
        Args:
            meeting: Meeting object
            
        Returns:
            Condensed summary if exists, None otherwise
        """
        return meeting.condensed_summary
    
    def needs_condensation(self, meeting: Meeting) -> bool:
        """
        Check if meeting needs condensation.
        
        A meeting needs condensation if:
        - It has notes
        - It has not been condensed yet, OR
        - Notes have been updated since last condensation
        
        Args:
            meeting: Meeting object
            
        Returns:
            True if condensation needed
        """
        # Scope to meeting date — same rationale as condense_meeting
        meeting_date = meeting.start_time.date()
        notes = self.session.query(Note).filter(
            Note.meeting_id == meeting.id,
            Note.created_date == meeting_date,
            ~Note.tags.op('@>')(['info-only']),
            Note.source != 'condensed'
        ).all()
        
        if not notes:
            return False
        
        # Never condensed
        if not meeting.condensed_at:
            return True
        
        # Check if any notes updated after condensation
        latest_note_update = max(note.updated_at for note in notes)
        return latest_note_update > meeting.condensed_at


# Singleton instance
_note_condenser_instance: Optional[NoteCondenser] = None


def get_note_condenser(session: Session) -> NoteCondenser:
    """
    Get NoteCondenser instance.
    
    Note: Not a true singleton since it requires a session.
    Each call creates a new instance with the provided session.
    
    Args:
        session: Database session
        
    Returns:
        NoteCondenser instance
    """
    return NoteCondenser(session)
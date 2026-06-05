"""
WorkmAIn Note Condenser
Note Condenser v2.1
20260605

AI-powered condensation of meeting notes into one-line summaries for Clockify.

Takes multiple meeting notes and condenses them into a professional, concise summary
suitable for time tracking entries.

Version History:
- v1.0: Initial implementation with Claude integration
- v1.1: Fixed session attachment issue - now queries meeting from database
- v1.2: Added writing style context integration for consistent voice (Phase 5)
- v1.3: Phase 5.1 - Filter out info-only (#ifo) notes from condensation
- v1.4: Phase 5.1 - Return default "Attended <Meeting>" when all notes are #ifo
- v1.5: Hotfix - exclude source='meeting' (prior condensed summary notes) from
        condensation query so auto-generated notes don't pollute AI input
- v1.6: Hotfix fix - filter on source='condensed' instead of source='meeting'
        since notes log also uses source='meeting' for regular user notes
- v1.7: Hotfix - scope notes query to meeting date (Note.created_date == meeting_date)
        so notes from previous recurring occurrences sharing the same meeting_id are
        not included; fixes stale content reappearing after user deletes today's notes
- v1.8: Gate 2 cost tracking sprint — replace hardcoded self.claude with provider_manager
        routing through 'note_condensation' config entry; persist ai_costs row after
        each condensation; honours provider parameter as provider_override
- v1.9: Provider Foundation Sprint — remove get_claude_client/get_gemini_client imports
        and register_provider() calls; ProviderManager._load_config() now instantiates
        providers from PROVIDER_REGISTRY directly
- v2.0: Hotfix — raise max_tokens 200→1024; Gemini 2.5 Flash uses thinking tokens from
        the max_output_tokens budget, leaving insufficient space for the visible response
- v2.1: Gate 0 Phase 13 Sprint 1 (20260605) — replace broken _format_writing_style_context
        with StyleAdapter.get_style_prompt("internal") for consistent voice
        across condensation and reports
"""

from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from workmain.database.models import Meeting, Note
from workmain.ai.base_provider import GenerationRequest, ProviderType
from workmain.ai.cost_tracker import get_cost_tracker
from workmain.ai.provider_manager import get_provider_manager
from workmain.database.repositories.ai_costs_repo import AiCostRepository
from workmain.templates_engine import get_style_adapter


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
    ) -> str:
        """
        Condense all notes from a meeting into a single summary.
        
        Args:
            meeting: Meeting object with notes to condense
            provider: AI provider to use (defaults to Claude)
            
        Returns:
            Condensed one-line summary
            
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
        
        if not notes:
            # All notes are info-only (#ifo), return default message
            default_summary = f"Attended {db_meeting.title}"
            db_meeting.condensed_summary = default_summary
            db_meeting.condensed_at = datetime.now()
            self.session.commit()
            return default_summary
        
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

            return db_meeting.condensed_summary

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
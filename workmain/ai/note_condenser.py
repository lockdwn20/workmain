"""
WorkmAIn Note Condenser
Note Condenser v1.0
20251231

AI-powered condensation of meeting notes into one-line summaries for Clockify.

Takes multiple meeting notes and condenses them into a professional, concise summary
suitable for time tracking entries.

Version History:
- v1.0: Initial implementation with Claude integration
"""

from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from workmain.database.models import Meeting, Note
from workmain.ai.base_provider import GenerationRequest, ProviderType
from workmain.ai.claude_client import get_claude_client
from workmain.ai.cost_tracker import get_cost_tracker


class NoteCondenser:
    """
    AI-powered note condensation for meetings.
    
    Condenses multiple meeting notes into a single professional summary
    suitable for Clockify time entry descriptions.
    """
    
    def __init__(self, session: Session):
        """
        Initialize note condenser.
        
        Args:
            session: Database session for queries and updates
        """
        self.session = session
        self.claude = get_claude_client()
        self.cost_tracker = get_cost_tracker()
    
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
        # Get all notes for this meeting
        notes = self.session.query(Note).filter(
            Note.meeting_id == meeting.id
        ).order_by(Note.created_at).all()
        
        if not notes:
            raise ValueError(f"Meeting '{meeting.title}' has no notes to condense")
        
        # Build condensation prompt
        prompt = self._build_condensation_prompt(meeting, notes)
        
        # Generate condensed summary
        request = GenerationRequest(
            prompt=prompt,
            max_tokens=200,  # One-liner shouldn't need more
            temperature=0.3,  # Low temperature for consistency
            system_prompt=self._get_system_prompt()
        )
        
        # Track cost
        self.cost_tracker.start_report(f"condense_{meeting.title}", datetime.now().date())
        
        try:
            # Generate with Claude (or specified provider)
            response = self.claude.generate(request)
            
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
            meeting.condensed_summary = response.content.strip()
            meeting.condensed_at = datetime.now()
            self.session.commit()
            
            return meeting.condensed_summary
            
        finally:
            self.cost_tracker.end_report(0.0)  # No generation time tracking needed
    
    def _build_condensation_prompt(
        self,
        meeting: Meeting,
        notes: List[Note]
    ) -> str:
        """
        Build the prompt for AI condensation.
        
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
        
        prompt = f"""Condense the following meeting notes into a single professional one-line summary suitable for a time tracking entry.

Meeting: {meeting.title}
Duration: {meeting.duration_hours:.1f} hours
Date: {meeting.start_time.strftime('%Y-%m-%d')}

Notes:
{notes_text}

Requirements:
1. Create ONE concise sentence (max 200 characters)
2. Use professional, action-oriented language
3. Include key topics, decisions, or blockers
4. Format: "<Meeting type>: <key points>"
5. Do NOT include tags, formatting, or metadata
6. Be specific and concrete

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
        # Get notes
        notes = self.session.query(Note).filter(
            Note.meeting_id == meeting.id
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

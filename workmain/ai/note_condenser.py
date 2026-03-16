"""
WorkmAIn Note Condenser
Note Condenser v1.5
20260313

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
"""

import json
from typing import List, Optional
from datetime import datetime
from pathlib import Path

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
        self.claude = get_claude_client()
        self.cost_tracker = get_cost_tracker()
        self.writing_style = self._load_writing_style()
    
    def _load_writing_style(self) -> dict:
        """
        Load writing style configuration.
        
        Returns:
            dict: Writing style settings, or empty dict if file not found
        """
        style_path = Path("templates/style/writing_style.json")
        
        if not style_path.exists():
            # Return empty style if file doesn't exist
            return {}
        
        try:
            with open(style_path, 'r') as f:
                return json.load(f)
        except Exception:
            # If load fails, return empty dict (don't break condensation)
            return {}
    
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
        
        # Get all notes for this meeting, excluding info-only (#ifo) notes and
        # auto-generated condensed summary notes (source='meeting')
        notes = self.session.query(Note).filter(
            Note.meeting_id == db_meeting.id,
            ~Note.tags.op('@>')(['info-only']),
            Note.source != 'meeting'
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
            max_tokens=200,  # One-liner shouldn't need more
            temperature=0.3,  # Low temperature for consistency
            system_prompt=self._get_system_prompt()
        )
        
        # Track cost
        self.cost_tracker.start_report(f"condense_{db_meeting.title}", datetime.now().date())
        
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
            db_meeting.condensed_summary = response.content.strip()
            db_meeting.condensed_at = datetime.now()
            self.session.commit()
            
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
        
        # Add writing style context if available
        if self.writing_style:
            style_context = self._format_writing_style_context()
            prompt = f"""{style_context}

{prompt}"""
        
        # Add requirements
        prompt += """

Requirements:
1. Create ONE concise sentence (max 200 characters)
2. Use professional, action-oriented language
3. Include key topics, decisions, or blockers
4. Format: "<Meeting type>: <key points>"
5. Do NOT include tags, formatting, or metadata
6. Be specific and concrete"""
        
        # Add style matching requirement if we have style
        if self.writing_style:
            prompt += "\n7. Match the established writing style and voice shown above"
        
        # Add examples
        prompt += """

Example formats:
- "Team standup: Fixed authentication bug, discussed Q1 roadmap, blocked on API keys"
- "Client review: Presented dashboard mockups, received approval for phase 2, scheduled follow-up"
- "Sprint planning: Estimated 23 story points, assigned tasks, identified 2 blockers"

Condensed summary:"""
        
        return prompt
    
    def _format_writing_style_context(self) -> str:
        """
        Format writing style information for inclusion in prompt.
        
        Returns:
            Formatted writing style context string
        """
        if not self.writing_style:
            return ""
        
        context_parts = ["WRITING STYLE CONTEXT:"]
        
        # Add voice characteristics
        if "voice_characteristics" in self.writing_style:
            voice = ", ".join(self.writing_style["voice_characteristics"])
            context_parts.append(f"Voice: {voice}")
        
        # Add tone
        if "tone" in self.writing_style:
            context_parts.append(f"Tone: {self.writing_style['tone']}")
        
        # Add example phrases (limit to 3 for brevity)
        if "example_phrases" in self.writing_style:
            examples = self.writing_style["example_phrases"][:3]
            if examples:
                context_parts.append("\nExample phrases in this style:")
                for phrase in examples:
                    context_parts.append(f"- {phrase}")
        
        return "\n".join(context_parts)
    
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
        # Get notes, excluding info-only (#ifo) notes and condensed summary notes
        notes = self.session.query(Note).filter(
            Note.meeting_id == meeting.id,
            ~Note.tags.op('@>')(['info-only']),
            Note.source != 'meeting'
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
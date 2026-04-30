"""
WorkmAIn AI Prompt Builder
Prompt Builder v1.6
20260430

Dynamic prompt construction for AI report generation.

Features:
- Integrates template structure with database data
- Applies user's writing style
- Includes Master Log examples for context
- Manages context window limits
- Builds system and user prompts
- Supports both Claude and Gemini formats

Version History:
- v1.0: Initial implementation
- v1.1: Fixed to use StyleAdapter.get_style_prompt() instead of non-existent get_style_for_ai()
- v1.2: Fixed repository method names (get_date_range not get_by_date_range),
        meetings query directly since no get_date_range method exists
- v1.3: Phase 5.1 - Fixed meeting.duration_minutes (computed from start/end),
        entry.duration_hours (was duration_minutes), attendees count
- v1.4: Phase 5.1 - Removed redundant Python-level tag filtering in _get_filtered_notes;
        database-level filtering via notes_repo.get_date_range is sufficient
- v1.5: Fixed tag_filter key mismatch (was tags_filter); now matches template format
- v1.6: Hotfix eod-backdate-bugs-2 — always include individual time entry descriptions
        in every section's context (not just time_tracking/summary); project-level
        summary still gated; fixes backdated reports missing non-meeting work entries

Workflow:
1. Load template structure
2. Get relevant data from database (filtered by tags)
3. Load user's writing style preferences
4. Select relevant Master Log examples
5. Build comprehensive prompt
6. Manage token limits
"""

from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from sqlalchemy.orm import Session

from workmain.templates_engine import (
    get_template_loader,
    get_style_adapter,
    TemplateLoader,
    StyleAdapter
)
from workmain.database.repositories.notes_repo import NotesRepository
from workmain.database.repositories.time_entries_repo import TimeEntriesRepository
from workmain.database.repositories.meetings_repo import MeetingsRepository


class PromptBuilder:
    """
    Build AI prompts for report generation.
    
    Combines template structure, database data, writing style,
    and Master Log examples into effective prompts.
    """
    
    def __init__(
        self,
        session: Session,
        template_loader: Optional[TemplateLoader] = None,
        style_adapter: Optional[StyleAdapter] = None
    ):
        """
        Initialize prompt builder.
        
        Args:
            session: Database session
            template_loader: Template loader instance (optional)
            style_adapter: Style adapter instance (optional)
        """
        self.session = session
        self.template_loader = template_loader or get_template_loader()
        self.style_adapter = style_adapter or get_style_adapter()
        
        # Initialize repositories
        self.notes_repo = NotesRepository(session)
        self.time_repo = TimeEntriesRepository(session)
        self.meetings_repo = MeetingsRepository(session)
    
    def build_prompt(
        self,
        template_name: str,
        report_date: date,
        section_name: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Build complete prompt for report generation.
        
        Args:
            template_name: Name of template to use
            report_date: Date for the report
            section_name: Optional - generate only this section
            
        Returns:
            Tuple of (system_prompt, user_prompt)
            
        Raises:
            ValueError: If template not found or invalid
        """
        # Load template
        template = self.template_loader.load(template_name)
        
        # Get report metadata
        metadata = template.get("metadata", {})
        report_type = metadata.get("type", template_name)
        
        # Build system prompt
        system_prompt = self._build_system_prompt(template, report_type)
        
        # Build user prompt
        user_prompt = self._build_user_prompt(
            template=template,
            report_date=report_date,
            section_name=section_name
        )
        
        return system_prompt, user_prompt
    
    def _build_system_prompt(
        self,
        template: Dict[str, Any],
        report_type: str
    ) -> str:
        """
        Build system prompt with role, style, and guidelines.
        
        Args:
            template: Template dictionary
            report_type: Type of report being generated
            
        Returns:
            System prompt string
        """
        # Get writing style as formatted prompt
        style_prompt = self.style_adapter.get_style_prompt(
            "internal" if "internal" in report_type else "client"
        )
        
        # Get template metadata
        metadata = template.get("metadata", {})
        description = metadata.get("description", "")
        
        # Build system prompt
        parts = []
        
        # Role definition
        parts.append("You are a professional technical writer generating work reports.")
        parts.append(f"You are creating a {report_type.replace('_', ' ')} report.")
        
        if description:
            parts.append(f"Purpose: {description}")
        
        # Writing style (already formatted by style_adapter)
        if style_prompt:
            parts.append("\n# Writing Style")
            parts.append(style_prompt)
        
        # Output format
        parts.append("\n# Output Format")
        parts.append("Generate the report in well-structured markdown format.")
        parts.append("Follow the section structure provided in the prompt.")
        parts.append("Use the provided data to populate each section.")
        parts.append("Maintain consistency with the writing style guidelines.")
        
        # Quality guidelines
        parts.append("\n# Quality Guidelines")
        parts.append("- Be specific and concrete with examples")
        parts.append("- Focus on technical accuracy")
        parts.append("- Maintain appropriate level of detail for the audience")
        parts.append("- Use active voice where possible")
        parts.append("- Keep sentences clear and concise")
        
        return "\n".join(parts)
    
    def _build_user_prompt(
        self,
        template: Dict[str, Any],
        report_date: date,
        section_name: Optional[str] = None
    ) -> str:
        """
        Build user prompt with template structure and data.
        
        Args:
            template: Template dictionary
            report_date: Date for the report
            section_name: Optional specific section
            
        Returns:
            User prompt string
        """
        parts = []
        
        # Header with date and context
        parts.append(f"# Report Generation Request")
        parts.append(f"Date: {report_date.strftime('%Y-%m-%d')}")
        parts.append(f"Template: {template.get('metadata', {}).get('name', 'Unknown')}")
        parts.append("")
        
        # Get sections to generate
        sections = template.get("sections", [])
        if section_name:
            sections = [s for s in sections if s.get("name") == section_name]
        
        if not sections:
            raise ValueError(f"Section '{section_name}' not found in template")
        
        # Add data for each section
        parts.append("# Data to Include")
        parts.append("")
        
        for section in sections:
            section_data = self._get_section_data(
                section=section,
                report_date=report_date,
                template=template
            )
            
            if section_data:
                parts.append(f"## {section.get('title', 'Section')}")
                parts.append(section_data)
                parts.append("")
        
        # Add Master Log examples if available
        master_log_examples = self._get_master_log_examples(template, report_date)
        if master_log_examples:
            parts.append("# Style Reference Examples")
            parts.append("Here are examples from past reports showing the desired style and format:")
            parts.append("")
            parts.append(master_log_examples)
            parts.append("")
        
        # Generation instructions
        parts.append("# Generation Instructions")
        parts.append("Using the above data and style guidelines, generate a complete report.")
        parts.append("Follow the template structure and maintain the established writing style.")
        parts.append("Be specific and use concrete examples from the provided data.")
        
        return "\n".join(parts)
    
    def _get_section_data(
        self,
        section: Dict[str, Any],
        report_date: date,
        template: Dict[str, Any]
    ) -> str:
        """
        Get data for a specific section.
        
        Args:
            section: Section configuration
            report_date: Report date
            template: Full template
            
        Returns:
            Formatted data string
        """
        section_type = section.get("type", "custom")
        tag_filter = section.get("tag_filter", {})
        tags_include = tag_filter.get("include", [])
        tags_exclude = tag_filter.get("exclude", [])
        
        parts = []
        
        # Get date range for the section
        date_range = self._get_date_range(template, report_date)
        start_date, end_date = date_range
        
        # Get notes
        notes = self._get_filtered_notes(
            start_date=start_date,
            end_date=end_date,
            tags_include=tags_include,
            tags_exclude=tags_exclude
        )
        
        if notes:
            parts.append("### Notes:")
            for note in notes:
                tags_str = ", ".join(f"[{tag}]" for tag in note.get("tags", []))
                timestamp = note.get("created_at", "")
                content = note.get("content", "")
                parts.append(f"- {timestamp} {tags_str}: {content}")
        
        # Always include individual work entry descriptions so every section has full
        # context — critical for backdated reports where notes may have the wrong
        # created_date but time entries always filter by entry_date correctly.
        time_entries = self._get_time_entries(start_date, end_date)
        if time_entries:
            parts.append("\n### Work Entries:")
            for entry in time_entries:
                time_str = entry.get("start_time") or ""
                hours = entry.get("duration_hours", 0)
                desc = entry.get("description") or ""
                parts.append(f"- {time_str} ({hours}h): {desc}")

        # Project-level time tracking summary only for time_tracking/summary sections
        if section_type in ["time_tracking", "summary"] and time_entries:
            parts.append("\n### Time Tracking Summary:")
            total_hours = sum(e.get("duration_hours", 0) for e in time_entries)
            parts.append(f"Total time logged: {total_hours:.2f} hours")

            by_project: Dict[str, float] = {}
            for entry in time_entries:
                project = entry.get("project_name") or "General"
                by_project[project] = by_project.get(project, 0) + entry.get("duration_hours", 0)

            parts.append("\nBy project:")
            for project, hours in sorted(by_project.items()):
                parts.append(f"- {project}: {hours:.2f} hours")
        
        # Get meetings
        meetings = self._get_meetings(start_date, end_date)
        if meetings:
            parts.append("\n### Meetings:")
            for meeting in meetings:
                time_str = meeting.get("start_time", "")
                title = meeting.get("title", "Untitled")
                attendees = meeting.get("attendees", 0)
                parts.append(f"- {time_str} - {title} ({attendees} attendees)")
        
        return "\n".join(parts) if parts else "No data available for this section."
    
    def _get_date_range(
        self,
        template: Dict[str, Any],
        report_date: date
    ) -> Tuple[date, date]:
        """
        Calculate date range based on template metadata.
        
        Args:
            template: Template dictionary
            report_date: Report date
            
        Returns:
            Tuple of (start_date, end_date)
        """
        metadata = template.get("metadata", {})
        frequency = metadata.get("frequency", "daily")
        
        if frequency == "daily":
            return report_date, report_date
        elif frequency == "weekly":
            # Get Monday to Friday of the week containing report_date
            days_since_monday = report_date.weekday()
            start_date = report_date - timedelta(days=days_since_monday)
            end_date = start_date + timedelta(days=4)  # Friday
            return start_date, end_date
        elif frequency == "monthly":
            # First to last day of month
            start_date = report_date.replace(day=1)
            if report_date.month == 12:
                end_date = date(report_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(report_date.year, report_date.month + 1, 1) - timedelta(days=1)
            return start_date, end_date
        else:
            # Default to single day
            return report_date, report_date
    
    def _get_filtered_notes(
        self,
        start_date: date,
        end_date: date,
        tags_include: List[str],
        tags_exclude: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get notes filtered by date and tags.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            tags_include: Tags that must be present
            tags_exclude: Tags that must not be present

        Returns:
            List of note dictionaries
        """
        # Database-level filtering handles tag inclusion/exclusion
        notes = self.notes_repo.get_date_range(
            start_date=start_date,
            end_date=end_date,
            include_tags=tags_include if tags_include else None,
            exclude_tags=tags_exclude if tags_exclude else None
        )

        # Convert to dictionaries (filtering already done by repository)
        return [{
            "content": note.content,
            "tags": list(note.tags or []),
            "created_at": note.created_at.strftime("%Y-%m-%d %H:%M") if note.created_at else ""
        } for note in notes]
    
    def _get_time_entries(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get time entries for date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of time entry dictionaries
        """
        entries = self.time_repo.get_date_range(  # ← Fixed: get_date_range not get_by_date_range
            start_date=start_date,
            end_date=end_date
        )
        
        return [{
            "project_name": entry.project.name if entry.project else None,
            "start_time": entry.entry_time.strftime("%H:%M") if entry.entry_time else None,
            "duration_hours": float(entry.duration_hours),
            "description": entry.description
        } for entry in entries]
    
    def _get_meetings(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get meetings for date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of meeting dictionaries
        """
        from workmain.database.models import Meeting
        from sqlalchemy import and_
        
        # Convert dates to datetimes for query
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        
        # Query meetings directly (MeetingsRepository doesn't have get_date_range)
        meetings = self.session.query(Meeting).filter(
            and_(
                Meeting.start_time >= start_dt,
                Meeting.start_time <= end_dt
            )
        ).order_by(Meeting.start_time).all()
        
        return [{
            "title": meeting.title,
            "start_time": meeting.start_time.strftime("%H:%M"),
            "duration_minutes": int((meeting.end_time - meeting.start_time).total_seconds() / 60),
            "attendees": len(meeting.attendees) if meeting.attendees else 0
        } for meeting in meetings]
    
    def _get_master_log_examples(
        self,
        template: Dict[str, Any],
        report_date: date
    ) -> str:
        """
        Get relevant examples from Master Logs.
        
        Args:
            template: Template dictionary
            report_date: Report date
            
        Returns:
            Formatted examples string
        """
        # Check if Master Log examples exist
        project_root = Path(__file__).parent.parent.parent
        master_logs_dir = project_root / "docs" / "master_logs"
        
        if not master_logs_dir.exists():
            return ""
        
        # Find relevant .docx files
        # Note: For now, we'll just note that examples are available
        # Full docx parsing would require python-docx
        docx_files = list(master_logs_dir.glob("*.docx"))
        
        if not docx_files:
            return ""
        
        parts = []
        parts.append("Reference Master Log reports are available in docs/master_logs/")
        parts.append("These demonstrate the expected format, style, and level of detail.")
        parts.append("Match the professional tone and structure shown in these examples.")
        
        return "\n".join(parts)
    
    def estimate_tokens(self, system_prompt: str, user_prompt: str) -> int:
        """
        Estimate token count for prompts.
        
        Args:
            system_prompt: System prompt string
            user_prompt: User prompt string
            
        Returns:
            Estimated token count
            
        Note:
            Uses rough estimate of 1 token ≈ 4 characters
            For more accuracy, use actual tokenizer
        """
        total_chars = len(system_prompt) + len(user_prompt)
        return total_chars // 4


# Singleton instance
_prompt_builder_instance: Optional[PromptBuilder] = None


def get_prompt_builder(session: Session) -> PromptBuilder:
    """
    Get singleton prompt builder instance.
    
    Args:
        session: Database session
        
    Returns:
        PromptBuilder instance
        
    Note:
        Session is required, so singleton pattern is simplified
        Each call with different session returns new instance
    """
    return PromptBuilder(session)
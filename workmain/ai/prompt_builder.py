"""
WorkmAIn AI Prompt Builder
Prompt Builder v2.3
20260724

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
- v1.7: Phase 11 Gate 6 — build_prompt() accepts filter_client and client_id;
        stores on instance; private data-fetch methods use get_for_date_client()
- v1.8: Hotfix weekly-report-ai-instruction — include ai_instruction per section in
        the user prompt; was defined in every template but never read, causing the
        weekly client report to ignore tag semantics and incorporate internal content
- v1.9: Hotfix weekly-report-data-sources — _get_section_data now respects the
        data_sources field declared in each template section; time entries and meetings
        are only fetched when listed (e.g. only section 1 of weekly_client declares
        time_entries); for client reports (filter_client=True) the Work Entries header
        carries an explicit context-only note so the AI anchors on tagged notes
- v2.0: Phase 13 DB Schema Sprint Gate 5 — _get_time_entries reads entry.note.content
        instead of the now-dropped entry.description column
- v2.1: Phase 13 Sprint 2 Gate 1a — add build_weekly_prompt(); prepends confirmed
        daily summaries block when calling build_prompt() for weekly_client reports;
        build_prompt() unmodified
- v2.2: Hotfix items-33-34-incomplete-impl — rewrite build_weekly_prompt() (Item 34):
        (1) prefer corrected_content over content for each confirmed daily;
        (2) substitutive path — when all 5 Mon–Fri weekdays are confirmed, lean
        user_prompt replaces raw DB data entirely (token reduction);
        (3) fallback to raw build_prompt() when any weekday lacks a confirmed daily
- v2.3: Item #61 Gate 3 (Design Rules 6-7) — build_weekly_prompt() removed
        entirely, retiring the confirmed-substitutive branch outright. Per
        RECON_SPEC_ITEM46_WEEKLY_PROMPT_BUILDER_20260724.md, build_prompt()
        (via _get_section_data()) already resolves the correct Mon–Fri
        window for any frequency: "weekly" template and already applies
        each section's exact tag_filter include/exclude lists — nothing
        new was built, weekly generation now always takes the path that
        already ran on every Thursday call. Resolves Backlog Item #46 in
        full (weekday-coverage gating, Thursday-draft-unreachable-confirmed
        path, and internal-content pollution via unfiltered daily-body
        injection) as a side effect of removing the code path that caused
        all three. get_db/ReportsRepository imports dropped (no longer
        used in this file — that was the method's only caller of either).

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

        # Client filter state — set by build_prompt() before each report
        self._filter_client: bool = False
        self._client_id: Optional[int] = None
    
    def build_prompt(
        self,
        template_name: str,
        report_date: date,
        section_name: Optional[str] = None,
        filter_client: bool = False,
        client_id: Optional[int] = None,
    ) -> Tuple[str, str]:
        """
        Build complete prompt for report generation.

        Args:
            template_name: Name of template to use
            report_date: Date for the report
            section_name: Optional - generate only this section
            filter_client: When True, restrict data queries to client_id records only
            client_id: Client ID for filtering (only applied when filter_client=True)

        Returns:
            Tuple of (system_prompt, user_prompt)

        Raises:
            ValueError: If template not found or invalid
        """
        # Store filter context for private helper methods
        self._filter_client = filter_client
        self._client_id = client_id

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
                ai_instruction = section.get("ai_instruction", "")
                if ai_instruction:
                    parts.append(f"**Instruction:** {ai_instruction}")
                    parts.append("")
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

        # Respect data_sources declared in the template section. When absent or
        # empty, default to all sources (backward compat). When explicitly declared,
        # only fetch what is listed — prevents untagged time entries from leaking
        # into client-facing sections that have no use for them.
        data_sources = section.get("data_sources", [])
        include_time_entries = ("time_entries" in data_sources) if data_sources else True
        include_meetings = ("meetings" in data_sources) if data_sources else True

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

        # Fetch time entries only when the section declares "time_entries" in
        # data_sources. Individual descriptions provide context for backdated
        # reports where entry_date is reliable but note created_date may not be.
        if include_time_entries:
            time_entries = self._get_time_entries(start_date, end_date)
            if time_entries:
                if self._filter_client:
                    parts.append(
                        "\n### Work Entries (time allocation context only — "
                        "use the tagged notes above as the authoritative source "
                        "for client-facing content; do not derive report items "
                        "from time entry descriptions alone):"
                    )
                else:
                    parts.append("\n### Work Entries:")
                for entry in time_entries:
                    time_str = entry.get("start_time") or ""
                    hours = entry.get("duration_hours", 0)
                    desc = entry.get("description") or ""
                    parts.append(f"- {time_str} ({hours}h): {desc}")

                # Project-level time tracking summary only for time_tracking/summary sections
                if section_type in ["time_tracking", "summary"]:
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

        # Fetch meetings only when the section declares "meetings" in data_sources.
        if include_meetings:
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
        # Database-level filtering handles tag inclusion/exclusion and client filter
        notes = self.notes_repo.get_for_date_client(
            start_date=start_date,
            end_date=end_date,
            include_tags=tags_include if tags_include else None,
            exclude_tags=tags_exclude if tags_exclude else None,
            client_id=self._client_id,
            filter_client=self._filter_client,
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
        entries = self.time_repo.get_for_date_client(
            start_date=start_date,
            end_date=end_date,
            client_id=self._client_id,
            filter_client=self._filter_client,
        )
        
        return [{
            "project_name": entry.project.name if entry.project else None,
            "start_time": entry.entry_time.strftime("%H:%M") if entry.entry_time else None,
            "duration_hours": float(entry.duration_hours),
            "description": entry.note.content,
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
        meetings = self.meetings_repo.get_for_date_client(
            start_date=start_date,
            end_date=end_date,
            client_id=self._client_id,
            filter_client=self._filter_client,
        )

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
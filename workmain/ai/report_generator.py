"""
WorkmAIn AI Report Generator
Report Generator v1.10
20260512

High-level orchestrator for AI report generation with database integration.

Features:
- Orchestrates full report generation pipeline
- Combines prompt_builder + AI clients + templates
- Handles section-by-section generation (optional)
- Saves reports to files (markdown, text)
- Saves report metadata to database for analytics
- Provides generation status and logging
- Manages errors and retries
- Tracks costs in database (not JSON file)

Version History:
- v1.0: Initial implementation
- v1.1: Fixed ProviderManager method calls (generate not generate_with_fallback),
        Added provider registration in __init__
- v1.2: Fixed CostTracker.track_section() calls to match signature:
        Added model, prompt_tokens, completion_tokens parameters
        Convert provider enum to string (.value)
- v1.3: Integrated database storage for reports and costs
        Added reports repository for database access
        Costs now stored in reports.report_metadata JSONB field
        Removed JSON file persistence
- v1.4: Fixed metadata column name (metadata → report_metadata) for SQLAlchemy compatibility
- v1.5: Added CostTracker lifecycle management (start_report/end_report)
        Fixed "No active report" error
- v1.6: Phase 5.1 - Added subject line to report output; gets subject_line from template,
        substitutes variables (day_name, date_long, user_full_name), includes in markdown header
- v1.7: Gate 0.1 - Updated default output_dir from reports/ to output/reports/
        for output directory restructure (Phase 6)
- v1.8: Hotfix staging-eod — renamed output/reports/ to staging/reports/
- v1.9: Phase 11 Gate 5 — generate_report() accepts client_id; passes to reports_repo.create()
- v1.10: Phase 11 Gate 6 — generate_report() accepts filter_client and client_id_filter;
         passes both to prompt_builder.build_prompt()

Workflow:
1. Load template and validate
2. Build prompts with prompt_builder
3. Start cost tracking (start_report)
4. Generate content with AI client
5. Track costs (track_section)
6. Format output
7. Save to file
8. Save to database with report_metadata (costs, tokens, provider)
9. End cost tracking (end_report with timing)
"""

from datetime import date, datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from enum import Enum
import time

from workmain.ai import (
    get_prompt_builder,
    get_provider_manager,
    get_cost_tracker,
    PromptBuilder,
    ProviderManager,
    CostTracker,
    GenerationRequest,
    GenerationResponse,
    ProviderType
)
from workmain.templates_engine import get_template_loader, TemplateLoader
from workmain.database.repositories.reports_repo import get_reports_repository, ReportsRepository


class ReportFormat(Enum):
    """Output format for generated reports."""
    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"


class ReportGenerator:
    """
    High-level orchestrator for AI report generation.
    
    Manages the complete pipeline from data to final report file.
    """
    
    def __init__(
        self,
        session: Session,
        prompt_builder: Optional[PromptBuilder] = None,
        provider_manager: Optional[ProviderManager] = None,
        cost_tracker: Optional[CostTracker] = None,
        template_loader: Optional[TemplateLoader] = None,
        reports_repository: Optional[ReportsRepository] = None,
        output_dir: Optional[Path] = None
    ):
        """
        Initialize report generator.
        
        Args:
            session: Database session
            prompt_builder: Prompt builder instance (optional)
            provider_manager: Provider manager instance (optional)
            cost_tracker: Cost tracker instance (optional)
            template_loader: Template loader instance (optional)
            reports_repository: Reports repository instance (optional)
            output_dir: Directory for saving reports (optional)
        """
        self.session = session
        self.prompt_builder = prompt_builder or get_prompt_builder(session)
        self.provider_manager = provider_manager or get_provider_manager()
        self.cost_tracker = cost_tracker or get_cost_tracker()
        self.template_loader = template_loader or get_template_loader()
        self.reports_repo = reports_repository or get_reports_repository(session)
        
        # Register AI providers with the manager
        from workmain.ai import get_claude_client, get_gemini_client
        claude = get_claude_client()
        gemini = get_gemini_client()
        self.provider_manager.register_provider(ProviderType.CLAUDE, claude)
        self.provider_manager.register_provider(ProviderType.GEMINI, gemini)
        
        # Set output directory
        if output_dir is None:
            project_root = Path(__file__).parent.parent.parent
            output_dir = project_root / "staging" / "reports"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(
        self,
        template_name: str,
        report_date: date,
        provider: Optional[ProviderType] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        save_to_file: bool = True,
        output_format: ReportFormat = ReportFormat.MARKDOWN,
        filename: Optional[str] = None,
        client_id: Optional[int] = None,
        filter_client: bool = False,
        client_id_filter: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate a complete report.

        Args:
            template_name: Name of template to use
            report_date: Date for the report
            provider: AI provider to use (None = use template default)
            max_tokens: Maximum tokens for generation
            temperature: Temperature for generation
            save_to_file: Whether to save report to file
            output_format: Output format
            filename: Custom filename (optional)
            client_id: Optional client ID for DB attribution (None = internal mode)
            filter_client: When True, prompt_builder restricts data to client_id_filter records
            client_id_filter: Client ID for data filtering in prompt_builder

        Returns:
            Dictionary with report content, metadata, and file path

        Raises:
            ValueError: If template not found or invalid
            GenerationError: If AI generation fails
        """
        # Start timing
        start_time = time.time()
        
        # Initialize cost tracking
        self.cost_tracker.start_report(template_name, report_date)
        
        try:
            # Load template
            template = self.template_loader.load(template_name)
            
            # Determine provider
            if provider is None:
                # Get from template metadata
                metadata = template.get("metadata", {})
                provider_name = metadata.get("ai_provider", "claude")
                provider = ProviderType.CLAUDE if provider_name == "claude" else ProviderType.GEMINI
            
            # Build prompts
            system_prompt, user_prompt = self.prompt_builder.build_prompt(
                template_name=template_name,
                report_date=report_date,
                filter_client=filter_client,
                client_id=client_id_filter,
            )

            # Create generation request
            request = GenerationRequest(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Generate with AI
            response, fallback_used = self.provider_manager.generate(
                request=request,
                report_type=template_name,
                provider_override=provider
            )
            
            # Track costs
            self.cost_tracker.track_section(
                section_name="full_report",
                provider=response.provider.value,
                model=response.model,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                cost=response.cost
            )
            
            # Format output
            content = self._format_output(
                response.content,
                output_format=output_format,
                template=template,
                report_date=report_date
            )
            
            # Save to file if requested
            file_path = None
            if save_to_file:
                file_path = self._save_report(
                    content=content,
                    template_name=template_name,
                    report_date=report_date,
                    output_format=output_format,
                    filename=filename
                )
            
            # Calculate generation time
            generation_time = time.time() - start_time
            
            # Save to database
            db_report = self.reports_repo.create(
                report_type=template_name,
                report_date=report_date,
                content=content,
                ai_provider=response.provider.value,
                ai_model=response.model,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                total_tokens=response.tokens_used,
                cost=response.cost,
                generation_time=generation_time,
                file_path=str(file_path) if file_path else None,
                client_id=client_id,
            )
            
            # End cost tracking with generation time
            self.cost_tracker.end_report(generation_time)
            
            # Return result
            return {
                "content": content,
                "template_name": template_name,
                "report_date": report_date.isoformat(),
                "provider": response.provider.value,
                "model": response.model,
                "tokens_used": response.tokens_used,
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "cost": response.cost,
                "file_path": str(file_path) if file_path else None,
                "report_id": db_report.id,
                "generated_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            # End cost tracking on error (with 0 time)
            self.cost_tracker.end_report(0.0)
            raise
    
    def generate_section(
        self,
        template_name: str,
        section_name: str,
        report_date: date,
        provider: Optional[ProviderType] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate a single section of a report.
        
        Args:
            template_name: Name of template
            section_name: Name of section to generate
            report_date: Date for the report
            provider: AI provider to use
            max_tokens: Maximum tokens
            temperature: Temperature
            
        Returns:
            Dictionary with section content and metadata
        """
        # Start timing
        start_time = time.time()
        
        # Initialize cost tracking for this section
        self.cost_tracker.start_report(f"{template_name}_{section_name}", report_date)
        
        try:
            # Build prompts for specific section
            system_prompt, user_prompt = self.prompt_builder.build_prompt(
                template_name=template_name,
                report_date=report_date,
                section_name=section_name
            )
            
            # Determine provider
            if provider is None:
                template = self.template_loader.load(template_name)
                metadata = template.get("metadata", {})
                provider_name = metadata.get("ai_provider", "claude")
                provider = ProviderType.CLAUDE if provider_name == "claude" else ProviderType.GEMINI
            
            # Create request
            request = GenerationRequest(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Generate
            response, fallback_used = self.provider_manager.generate(
                request=request,
                report_type=template_name,
                provider_override=provider
            )
            
            # Track costs
            self.cost_tracker.track_section(
                section_name=section_name,
                provider=response.provider.value,
                model=response.model,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                cost=response.cost
            )
            
            # Calculate generation time
            generation_time = time.time() - start_time
            
            # End cost tracking
            self.cost_tracker.end_report(generation_time)
            
            return {
                "section_name": section_name,
                "content": response.content,
                "provider": response.provider.value,
                "tokens_used": response.tokens_used,
                "cost": response.cost
            }
        
        except Exception as e:
            # End cost tracking on error
            self.cost_tracker.end_report(0.0)
            raise
    
    def preview_report(
        self,
        template_name: str,
        report_date: date
    ) -> Dict[str, Any]:
        """
        Preview a report without generating AI content.
        
        Shows the prompts that would be sent to AI and estimated costs.
        
        Args:
            template_name: Name of template
            report_date: Date for the report
            
        Returns:
            Dictionary with prompts and estimates
        """
        # Build prompts
        system_prompt, user_prompt = self.prompt_builder.build_prompt(
            template_name=template_name,
            report_date=report_date
        )
        
        # Estimate tokens
        estimated_tokens = self.prompt_builder.estimate_tokens(system_prompt, user_prompt)
        
        # Load template for provider info
        template = self.template_loader.load(template_name)
        metadata = template.get("metadata", {})
        provider_name = metadata.get("ai_provider", "claude")
        
        # Estimate cost (rough)
        if provider_name == "claude":
            # Assume 50/50 split for completion
            estimated_cost = (estimated_tokens * 0.003 / 1000) + (estimated_tokens * 0.015 / 1000)
        else:
            # Gemini free tier
            estimated_cost = 0.0
        
        return {
            "template_name": template_name,
            "report_date": report_date.isoformat(),
            "provider": provider_name,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "estimated_tokens": estimated_tokens,
            "estimated_cost": estimated_cost
        }
    
    def _get_user_full_name(self) -> str:
        """
        Get user's full name from configuration.

        Returns:
            User's full name or default
        """
        import os
        from dotenv import load_dotenv

        load_dotenv()

        # Try environment variable first
        name = os.getenv('USER_FULL_NAME')

        if name:
            return name

        # Try config file
        try:
            from workmain.config_manager.loader import get_config
            config = get_config()
            name = config.get('user_preferences', 'user_full_name')

            if name:
                return name
        except Exception:
            pass

        # Default
        return "User Name"

    def _format_output(
        self,
        content: str,
        output_format: ReportFormat,
        template: Dict[str, Any],
        report_date: date
    ) -> str:
        """
        Format report content based on output format.

        Args:
            content: Generated content
            output_format: Desired output format
            template: Template dictionary
            report_date: Report date

        Returns:
            Formatted content
        """
        if output_format == ReportFormat.MARKDOWN:
            # Build subject line from template if present
            subject_line = None
            if template.get('subject_line'):
                # Get user full name and build variables
                user_full_name = self._get_user_full_name()
                variables = self.template_loader.build_variables(
                    report_date=report_date,
                    user_full_name=user_full_name
                )
                # Substitute variables in subject line
                subject_line = template['subject_line']
                for var_name, var_value in variables.items():
                    subject_line = subject_line.replace(f"{{{var_name}}}", str(var_value))

            # Already in markdown, just ensure header with subject line
            if not content.startswith("#"):
                title = template.get("name", "Report")
                header = f"# {title}\n"
                if subject_line:
                    header += f"**Subject:** {subject_line}\n"
                header += f"**Date:** {report_date.strftime('%B %d, %Y')}\n\n"
                content = header + content
            elif subject_line:
                # Content starts with # - insert subject line after first line
                lines = content.split('\n', 1)
                if len(lines) == 2:
                    content = f"{lines[0]}\n**Subject:** {subject_line}\n{lines[1]}"
                else:
                    content = f"{content}\n**Subject:** {subject_line}"
            return content
        
        elif output_format == ReportFormat.TEXT:
            # Strip markdown formatting
            import re
            # Remove markdown headers
            content = re.sub(r'^#+\s+', '', content, flags=re.MULTILINE)
            # Remove bold/italic
            content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
            content = re.sub(r'\*([^*]+)\*', r'\1', content)
            # Remove bullets
            content = re.sub(r'^\s*[-*]\s+', '  ', content, flags=re.MULTILINE)
            return content
        
        elif output_format == ReportFormat.HTML:
            # Convert markdown to HTML (basic)
            import re
            html = content
            # Headers
            html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
            html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
            html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
            # Bold
            html = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html)
            # Bullets
            html = re.sub(r'^\s*[-*]\s+(.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
            # Wrap in body
            html = f"<html><body>\n{html}\n</body></html>"
            return html
        
        return content
    
    def _save_report(
        self,
        content: str,
        template_name: str,
        report_date: date,
        output_format: ReportFormat,
        filename: Optional[str] = None
    ) -> Path:
        """
        Save report to file.
        
        Args:
            content: Report content
            template_name: Template name
            report_date: Report date
            output_format: Output format
            filename: Custom filename (optional)
            
        Returns:
            Path to saved file
        """
        # Determine filename
        if filename is None:
            ext = {
                ReportFormat.MARKDOWN: ".md",
                ReportFormat.TEXT: ".txt",
                ReportFormat.HTML: ".html"
            }[output_format]
            
            filename = f"{template_name}_{report_date.strftime('%Y-%m-%d')}{ext}"
        
        # Full path
        file_path = self.output_dir / filename
        
        # Save
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
    def get_report_history(
        self,
        template_name: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get history of generated reports from database.
        
        Args:
            template_name: Filter by template (optional)
            limit: Maximum number of reports
            
        Returns:
            List of report metadata dictionaries
        """
        reports = self.reports_repo.list_reports(
            report_type=template_name,
            limit=limit
        )
        
        return [
            {
                "template_name": report.report_type,
                "report_date": report.report_date.isoformat(),
                "file_path": report.report_metadata.get('file_path', '') if report.report_metadata else '',
                "file_size": Path(report.report_metadata.get('file_path', '')).stat().st_size 
                    if report.report_metadata and report.report_metadata.get('file_path') and Path(report.report_metadata.get('file_path')).exists() 
                    else 0,
                "created_at": report.created_at.isoformat()
            }
            for report in reports
        ]
    
    def get_cost_summary(self, report_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get cost summary for generated reports from database.
        
        Args:
            report_type: Filter by report type (optional)
            
        Returns:
            Cost summary dictionary
        """
        # Get summary from database
        summary = self.reports_repo.get_cost_summary()
        
        if report_type and summary['by_type'].get(report_type):
            # Return specific report type
            data = summary['by_type'][report_type]
            return {
                "report_type": report_type,
                "total_cost": data['cost'],
                "reports": data['reports'],
                "total_tokens": data['tokens']
            }
        elif report_type:
            # Report type not found
            return {"report_type": report_type, "total_cost": 0.0, "reports": 0}
        else:
            # Return full summary
            return summary


# Singleton instance
_report_generator_instance: Optional[ReportGenerator] = None


def get_report_generator(session: Session) -> ReportGenerator:
    """
    Get report generator instance.
    
    Args:
        session: Database session
        
    Returns:
        ReportGenerator instance
        
    Note:
        Session is required, so each call creates a new instance
        with the provided session
    """
    return ReportGenerator(session)
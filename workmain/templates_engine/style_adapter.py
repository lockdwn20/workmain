"""
WorkmAIn Style Adapter
Style Adapter v1.0
20251224

Adapts AI prompts to match user's writing style.
Injects style guidance into template rendering for Phase 4 AI integration.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class StyleAdapter:
    """
    Adapts AI prompts to match user's writing style.
    
    Loads writing style definitions and injects them into AI prompts
    to ensure generated content matches the user's voice and preferences.
    """
    
    def __init__(self, style_file: Optional[Path] = None):
        """
        Initialize style adapter.
        
        Args:
            style_file: Path to writing_style.json (default: templates/style/writing_style.json)
        """
        if style_file is None:
            project_root = Path(__file__).parent.parent.parent
            style_file = project_root / "templates" / "style" / "writing_style.json"
        
        self.style_file = Path(style_file)
        self.style = self._load_style()
    
    def _load_style(self) -> Dict:
        """Load writing style from JSON file."""
        try:
            with open(self.style_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Writing style file not found: {self.style_file}"
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {self.style_file}: {e}")
    
    def get_style_prompt(self, report_type: str = "internal") -> str:
        """
        Get style guidance prompt for AI.
        
        Args:
            report_type: Type of report (internal, client)
            
        Returns:
            Style guidance string to inject into AI prompt
        """
        guidance = self.style.get("ai_prompt_guidance", {})
        
        # Build prompt from style guidance
        prompt_parts = []
        
        # General guidance
        always_include = guidance.get("always_include", [])
        if always_include:
            prompt_parts.append("**Writing Style:**")
            for item in always_include:
                prompt_parts.append(f"- {item}")
        
        # Report-specific guidance
        if report_type == "internal":
            internal_specific = guidance.get("daily_internal_specific", [])
            if internal_specific:
                prompt_parts.append("\n**Internal Report Guidelines:**")
                for item in internal_specific:
                    prompt_parts.append(f"- {item}")
        elif report_type == "client":
            client_specific = guidance.get("weekly_client_specific", [])
            if client_specific:
                prompt_parts.append("\n**Client Report Guidelines:**")
                for item in client_specific:
                    prompt_parts.append(f"- {item}")
        
        # Formatting instructions
        formatting = guidance.get("formatting_instructions", [])
        if formatting:
            prompt_parts.append("\n**Formatting:**")
            for item in formatting:
                prompt_parts.append(f"- {item}")
        
        return "\n".join(prompt_parts)
    
    def get_section_style(self, section_name: str) -> Optional[Dict]:
        """
        Get style guidance for a specific section.
        
        Args:
            section_name: Section name (deliverables, accomplishments, etc.)
            
        Returns:
            Section style dict or None if not found
        """
        section_styles = self.style.get("section_specific_styles", {})
        return section_styles.get(section_name)
    
    def get_examples(self, context: Optional[str] = None) -> List[Dict]:
        """
        Get good and bad examples for training AI.
        
        Args:
            context: Filter examples by context (deliverable, blocker, etc.)
            
        Returns:
            List of example dicts
        """
        good_examples = self.style.get("good_examples", [])
        bad_examples = self.style.get("bad_examples", [])
        
        examples = {
            "good": good_examples,
            "bad": bad_examples
        }
        
        if context:
            # Filter by context
            examples["good"] = [
                ex for ex in good_examples 
                if ex.get("context", "").lower() == context.lower()
            ]
            examples["bad"] = [
                ex for ex in bad_examples 
                if ex.get("context", "").lower() == context.lower()
            ]
        
        return examples
    
    def get_examples_prompt(self, context: Optional[str] = None) -> str:
        """
        Get examples formatted for AI prompt.
        
        Args:
            context: Filter examples by context
            
        Returns:
            Formatted examples string
        """
        examples = self.get_examples(context)
        
        if not examples["good"] and not examples["bad"]:
            return ""
        
        prompt_parts = ["\n**Examples:**"]
        
        # Good examples
        if examples["good"]:
            prompt_parts.append("\n*Good examples:*")
            for ex in examples["good"]:
                prompt_parts.append(f"- \"{ex['text']}\"")
                prompt_parts.append(f"  (Why: {ex['why_good']})")
        
        # Bad examples
        if examples["bad"]:
            prompt_parts.append("\n*Avoid:*")
            for ex in examples["bad"]:
                prompt_parts.append(f"- \"{ex['text']}\"")
                prompt_parts.append(f"  (Why bad: {ex['why_bad']})")
        
        return "\n".join(prompt_parts)
    
    def build_ai_prompt(
        self,
        section_name: str,
        section_instruction: str,
        data: Dict,
        report_type: str = "internal"
    ) -> str:
        """
        Build complete AI prompt with style guidance.
        
        Args:
            section_name: Section name
            section_instruction: Base instruction from template
            data: Section data (notes, time entries, etc.)
            report_type: Type of report (internal, client)
            
        Returns:
            Complete AI prompt string
        """
        prompt_parts = []
        
        # Section instruction
        prompt_parts.append(section_instruction)
        
        # Style guidance
        style_prompt = self.get_style_prompt(report_type)
        if style_prompt:
            prompt_parts.append(f"\n{style_prompt}")
        
        # Section-specific style
        section_style = self.get_section_style(section_name)
        if section_style:
            prompt_parts.append("\n**Section Guidelines:**")
            if "focus" in section_style:
                prompt_parts.append(f"- Focus: {section_style['focus']}")
            if "example_pattern" in section_style:
                prompt_parts.append(f"- Pattern: {section_style['example_pattern']}")
            if "length" in section_style:
                prompt_parts.append(f"- Length: {section_style['length']}")
        
        # Examples
        examples_prompt = self.get_examples_prompt(section_name)
        if examples_prompt:
            prompt_parts.append(examples_prompt)
        
        # Data
        prompt_parts.append("\n**Data to work with:**")
        
        # Format notes
        if "notes" in data and data["notes"]:
            prompt_parts.append("\nNotes:")
            for note in data["notes"]:
                prompt_parts.append(f"- {note['content']}")
        
        # Format time entries
        if "time_entries" in data and data["time_entries"]:
            prompt_parts.append("\nTime spent:")
            for entry in data["time_entries"]:
                prompt_parts.append(
                    f"- {entry['description']} ({entry['duration_hours']}h)"
                )
        
        # Summary stats
        if "summary" in data:
            summary = data["summary"]
            prompt_parts.append("\nSummary:")
            if "total_hours" in summary:
                prompt_parts.append(f"- Total time: {summary['total_hours']}h")
            if "note_count" in summary:
                prompt_parts.append(f"- Number of items: {summary['note_count']}")
        
        # No data handling
        no_data_output = self.style.get("output_when_no_data", {}).get("default", "None at this time.")
        prompt_parts.append(f"\n**If no data:** Output exactly: \"{no_data_output}\"")
        
        return "\n".join(prompt_parts)
    
    def get_avoid_list(self) -> List[str]:
        """
        Get list of things to avoid in writing.
        
        Returns:
            List of things to avoid
        """
        return self.style.get("avoid", [])
    
    def get_principles(self) -> List[str]:
        """
        Get core writing principles.
        
        Returns:
            List of core principles
        """
        return self.style.get("core_principles", [])


# Singleton instance
_style_adapter = None


def get_style_adapter() -> StyleAdapter:
    """Get singleton StyleAdapter instance."""
    global _style_adapter
    if _style_adapter is None:
        _style_adapter = StyleAdapter()
    return _style_adapter

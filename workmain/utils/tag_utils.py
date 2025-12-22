"""
WorkmAIn Tag Utilities
Tag Parser v1.0
20251222

Provides tag parsing, validation, conversion, and display formatting.
Tags are case-insensitive, normalized, and validated against config/tags.json.
"""

import re
import json
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Set


class TagSystem:
    """
    Central tag management system.
    
    Handles:
    - Parsing tags from text (#ilo, #cr, etc.)
    - Validation against config
    - Short → full name conversion
    - Display formatting
    - Interactive correction prompts
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the tag system.
        
        Args:
            config_path: Path to tags.json. If None, uses config/tags.json
        """
        if config_path is None:
            # Default to config/tags.json relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "tags.json"
        
        self.config_path = config_path
        self.config = self._load_config()
        self.tag_mappings = self.config.get("tag_mappings", {})
        self.default_tag = self.config.get("default_tag", "ilo")
        self.validation = self.config.get("validation", {})
        self.display_options = self.config.get("display_options", {})
        
        # Build reverse mapping: full_name → short_name
        self.reverse_mappings = {
            v["full_name"]: k 
            for k, v in self.tag_mappings.items()
        }
    
    def _load_config(self) -> Dict:
        """Load tag configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Tag configuration not found at {self.config_path}. "
                "Please ensure config/tags.json exists."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {self.config_path}: {e}")
    
    def extract_tags(self, text: str) -> Tuple[str, List[str]]:
        """
        Extract hashtags from text.
        
        Args:
            text: Input text with potential hashtags
            
        Returns:
            Tuple of (text_without_tags, list_of_tag_shortcuts)
            
        Examples:
            "Fixed bug #ilo #cf" → ("Fixed bug", ["ilo", "cf"])
            "Meeting notes" → ("Meeting notes", [])
        """
        # Pattern matches #word (letters, numbers, hyphens, underscores)
        pattern = r'#([\w-]+)'
        
        # Find all tags
        tags = re.findall(pattern, text, re.IGNORECASE)
        
        # Remove tags from text
        clean_text = re.sub(pattern, '', text).strip()
        
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        # Lowercase tags (case-insensitive)
        tags = [tag.lower() for tag in tags]
        
        return clean_text, tags
    
    def validate_tags(self, tags: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate tags against configuration.
        
        Args:
            tags: List of tag shortcuts (e.g., ["ilo", "cf"])
            
        Returns:
            Tuple of (valid_tags, invalid_tags)
        """
        valid = []
        invalid = []
        
        for tag in tags:
            if tag.lower() in self.tag_mappings:
                valid.append(tag.lower())
            else:
                invalid.append(tag)
        
        return valid, invalid
    
    def convert_to_full_names(self, tags: List[str]) -> List[str]:
        """
        Convert tag shortcuts to full names.
        
        Args:
            tags: List of tag shortcuts (e.g., ["ilo", "cf"])
            
        Returns:
            List of full tag names (e.g., ["internal-only", "carry-forward"])
        """
        full_names = []
        
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower in self.tag_mappings:
                full_names.append(self.tag_mappings[tag_lower]["full_name"])
        
        return full_names
    
    def normalize_tags(self, tags: List[str]) -> List[str]:
        """
        Normalize tags: remove duplicates and optionally sort.
        
        Args:
            tags: List of full tag names
            
        Returns:
            Normalized list of tags
        """
        # Remove duplicates while preserving order
        seen: Set[str] = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)
        
        # Sort alphabetically if configured
        if self.validation.get("normalize_order", True):
            unique_tags.sort()
        
        return unique_tags
    
    def format_display(self, tags: List[str]) -> str:
        """
        Format tags for display.
        
        Args:
            tags: List of full tag names
            
        Returns:
            Formatted string (e.g., "[internal-only] [carry-forward]")
        """
        if not tags:
            return ""
        
        show_brackets = self.display_options.get("show_brackets", True)
        separator = self.display_options.get("separator", " ")
        
        if show_brackets:
            formatted = [f"[{tag}]" for tag in tags]
        else:
            formatted = tags
        
        return separator.join(formatted)
    
    def get_valid_tags_list(self) -> List[str]:
        """
        Get list of all valid tag shortcuts.
        
        Returns:
            List of valid tag shortcuts (e.g., ["ilo", "cr", "ifo", ...])
        """
        return sorted(self.tag_mappings.keys())
    
    def get_tag_description(self, tag_shortcut: str) -> Optional[str]:
        """
        Get description for a tag.
        
        Args:
            tag_shortcut: Tag shortcut (e.g., "ilo")
            
        Returns:
            Description string or None if tag not found
        """
        tag_lower = tag_shortcut.lower()
        if tag_lower in self.tag_mappings:
            return self.tag_mappings[tag_lower].get("description")
        return None
    
    def apply_default_tag(self, tags: List[str]) -> List[str]:
        """
        Apply default tag if no tags provided.
        
        Args:
            tags: List of tag shortcuts
            
        Returns:
            List with default tag added if empty, otherwise unchanged
        """
        if not tags and self.default_tag:
            return [self.default_tag]
        return tags
    
    def process_tags(
        self, 
        text: str, 
        apply_default: bool = True
    ) -> Tuple[str, List[str], List[str]]:
        """
        Complete tag processing pipeline.
        
        Args:
            text: Input text with hashtags
            apply_default: Whether to apply default tag if none found
            
        Returns:
            Tuple of (clean_text, valid_full_tags, invalid_tags)
            
        Example:
            >>> process_tags("Fixed bug #ilo #typo")
            ("Fixed bug", ["internal-only"], ["typo"])
        """
        # Extract tags from text
        clean_text, raw_tags = self.extract_tags(text)
        
        # Apply default if no tags found and requested
        if apply_default:
            raw_tags = self.apply_default_tag(raw_tags)
        
        # Validate tags
        valid_tags, invalid_tags = self.validate_tags(raw_tags)
        
        # Convert to full names
        full_tags = self.convert_to_full_names(valid_tags)
        
        # Normalize (remove duplicates, sort)
        normalized_tags = self.normalize_tags(full_tags)
        
        return clean_text, normalized_tags, invalid_tags
    
    def interactive_correction(
        self, 
        text: str, 
        invalid_tags: List[str],
        valid_tags: List[str]
    ) -> Optional[List[str]]:
        """
        Prompt user to correct invalid tags interactively.
        
        Args:
            text: Original text (for context)
            invalid_tags: List of invalid tag shortcuts
            valid_tags: List of valid tag shortcuts that were found
            
        Returns:
            List of corrected tag shortcuts, or None if user cancels
        """
        print(f"\n⚠️  Warning: Unknown tag(s): {', '.join(f'#{t}' for t in invalid_tags)}")
        print(f"Valid tags: {', '.join(f'#{t}' for t in self.get_valid_tags_list())}")
        
        # Show current valid tags
        if valid_tags:
            converted = self.convert_to_full_names(valid_tags)
            print(f"\nCurrent valid tags: {self.format_display(converted)}")
        
        print("\nOptions:")
        print("  1. Save note with valid tags only")
        print("  2. Correct the tags")
        print("  3. Cancel")
        
        choice = input("\nChoice (1-3): ").strip()
        
        if choice == "1":
            return valid_tags
        elif choice == "2":
            current_tags_str = " ".join(f"#{t}" for t in valid_tags) if valid_tags else ""
            prompt = f"Enter corrected tags (or press Enter to keep {current_tags_str or 'no tags'}): "
            corrected = input(prompt).strip()
            
            if not corrected:
                return valid_tags
            
            # Extract tags from corrected input
            _, new_tags = self.extract_tags(corrected)
            return new_tags
        elif choice == "3":
            return None
        else:
            print("Invalid choice. Cancelling.")
            return None
    
    def get_tags_for_report(self, report_type: str) -> List[str]:
        """
        Get list of tag full names that should be included in a report type.
        
        Args:
            report_type: Type of report (e.g., "daily_internal", "weekly_client")
            
        Returns:
            List of full tag names to include
        """
        included_tags = []
        
        for tag_config in self.tag_mappings.values():
            report_inclusion = tag_config.get("report_inclusion", {})
            if report_inclusion.get(report_type, False):
                included_tags.append(tag_config["full_name"])
        
        return included_tags


# Singleton instance for easy import
_tag_system_instance = None

def get_tag_system() -> TagSystem:
    """Get singleton instance of TagSystem."""
    global _tag_system_instance
    if _tag_system_instance is None:
        _tag_system_instance = TagSystem()
    return _tag_system_instance


# Convenience functions for common operations
def parse_tags(text: str, apply_default: bool = True) -> Tuple[str, List[str], List[str]]:
    """
    Convenience function: Parse and validate tags from text.
    
    Returns:
        (clean_text, valid_full_tags, invalid_tags)
    """
    ts = get_tag_system()
    return ts.process_tags(text, apply_default=apply_default)


def format_tags(tags: List[str]) -> str:
    """
    Convenience function: Format tags for display.
    
    Args:
        tags: List of full tag names
        
    Returns:
        Formatted string (e.g., "[internal-only] [carry-forward]")
    """
    ts = get_tag_system()
    return ts.format_display(tags)


def get_valid_tags() -> List[str]:
    """
    Convenience function: Get list of valid tag shortcuts.
    """
    ts = get_tag_system()
    return ts.get_valid_tags_list()
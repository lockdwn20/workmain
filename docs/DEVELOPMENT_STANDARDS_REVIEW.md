WorkmAIn
Development Standards Review v3.0
20260803

# WorkmAIn Development Standards Review

**Purpose:** Document established patterns and standards for the WorkmAIn project

**Version History:**
- v1.0 (20251224): Initial standards documentation
- v2.0 (20251226): Added version tracking locations and test organization standards
- v3.0 (20260803): Retired the version-header / version-history file pattern per the
  File Header Removal spec (v1.3). Module headers are now PEP 257 docstrings; git
  tags, `CHANGELOG.md`, and `workmain/__version__.py` are the version record.

---

## PATTERN REVIEW FROM EXISTING CODE

### 1. File Header Pattern (from tag_utils.py)

```python
"""
Provides tag parsing, validation, conversion, and display formatting.
Tags are case-insensitive, normalized, and validated against config/tags.json.
"""
```

**Standard:**
- PEP 257 module docstring: description only
- No version, no date, no version history block
- Git (tags, commit history, `CHANGELOG.md`) is the version record

### 2. Singleton Pattern (from tag_utils.py)

```python
# Singleton instance for easy import
_tag_system_instance = None

def get_tag_system() -> TagSystem:
    """Get singleton instance of TagSystem."""
    global _tag_system_instance
    if _tag_system_instance is None:
        _tag_system_instance = TagSystem()
    return _tag_system_instance
```

**Standard:**
- Module-level variable: `_<name>_instance = None`
- Function name: `get_<descriptive_name>()` - NOT just `get_validator()`
- Returns the class instance
- Creates on first call

### 3. Convenience Functions (from tag_utils.py)

```python
def parse_tags(text: str, apply_default: bool = True) -> Tuple[str, List[str], List[str]]:
    """
    Convenience function: Parse and validate tags from text.
    
    Returns:
        (clean_text, valid_full_tags, invalid_tags)
    """
    ts = get_tag_system()
    return ts.process_tags(text, apply_default=apply_default)
```

**Standard:**
- Module-level functions that call singleton
- Clear docstrings
- Type hints

### 4. Package __init__.py Pattern

```python
"""
Template system for report generation.
"""

from .loader import TemplateLoader, get_template_loader
from .validator import TemplateValidator, get_template_validator
from .field_manager import FieldManager
from .renderer import TemplateRenderer
from .style_adapter import StyleAdapter, get_style_adapter

__all__ = [
    'TemplateLoader',
    'get_template_loader',
    'TemplateValidator',
    'get_template_validator',
    'FieldManager',
    'TemplateRenderer',
    'StyleAdapter',
    'get_style_adapter',
]
```

**Standards:**
1. Descriptive module docstring
2. Import classes AND singleton functions
3. `__all__` lists all public exports
4. Descriptive names: `get_template_validator` NOT `get_validator`

### 5. Import Organization

From notes_repo.py:
```python
"""
Data access layer for notes with tag filtering and full-text search.
Handles all CRUD operations for the notes table.
"""

from datetime import date, datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, and_, or_, any_
from sqlalchemy.orm import Session

from workmain.database.models import Note, Meeting, Project
```

**Standard Order:**
1. Built-in imports (datetime, typing)
2. Third-party imports (sqlalchemy)
3. Local imports (workmain.*)

---

## NAMING CONVENTIONS

### Singleton Functions
- **Pattern**: `get_<descriptive_component_name>()`
- **Examples**:
  - `get_tag_system()` - NOT `get_tags()`
  - `get_template_loader()` - NOT `get_loader()`
  - `get_template_validator()` - NOT `get_validator()`
  - `get_style_adapter()` - NOT `get_adapter()`
  - `get_encryption()` - NOT `get_encryptor()`

### Why Descriptive Names?
- Clarity when importing: `from validator import get_template_validator`
- Avoids name collisions in namespaces
- Self-documenting code
- Consistent with existing pattern

---

## VERSION TRACKING LOCATIONS ⭐ NEW

### Where Versions ARE Tracked

**1. Git Tags:**
Each release merged to `main` is tagged `vX.Y.Z` and accompanied by a GitHub Release.

**2. CHANGELOG.md:**
Keep-a-Changelog format. Every release gets a `## [x.y.z]` section describing what
changed. This is the source of truth for release history.

**3. workmain/__version__.py (Project Level):**
```python
"""Current application version. See CHANGELOG.md for release history."""

__version__ = "1.28.0"
__version_info__ = (1, 28, 0)
__author__ = "Ray Race Jr."
__description__ = "Work Management AI - Intelligent personal work management system"
```

### Where Versions are NOT Tracked

**File headers (module docstrings):**
- ❌ Do NOT contain version numbers, dates, or a version-history block
- ✅ Description only (PEP 257 module docstring)
- Rationale: git already holds this history; duplicating it in every file invites drift

**file-structure.md:**
- ❌ Does NOT contain version numbers
- ✅ Contains structure and organization only
- Purpose: Map of where files belong
- Rationale: Structure changes less than versions

**implementation-checklist.md:**
- ❌ Does NOT contain version numbers
- ✅ Contains phase scope and deliverables
- Purpose: Master plan and roadmap
- Rationale: Focuses on "what to build" not "what version"

### Rationale

**Single Source of Truth:**
- Versions tracked in git tags, `CHANGELOG.md`, and `workmain/__version__.py`
- Git history provides the historical record
- Avoids duplication and sync issues

**Documentation Separation:**
- file-structure.md = "Where does it go?"
- CHANGELOG.md = "What version is it, and what changed?"
- implementation-checklist.md = "What should be built?"

### Getting Version Information

**Check current version:**
```bash
cat workmain/__version__.py
```

**Check release history:**
```bash
cat CHANGELOG.md
```

---

## TEST ORGANIZATION STANDARDS ⭐ NEW

### Directory Structure

```
tests/                          # Test suite root
├── conftest.py                 # pytest configuration
├── test_*.py                   # ✓ Test files (ROOT level)
├── fixtures/                   # Test data files
│   ├── sample_notes.json
│   └── sample_data.csv
└── mocks/                      # Mock implementations
    ├── mock_clockify.py        # Fake external services
    └── mock_outlook.py
```

### File Placement Rules

**test_*.py files:**
- ✅ Go in tests/ ROOT directory
- ❌ NOT in fixtures/ subdirectory
- ❌ NOT in mocks/ subdirectory
- Reason: pytest auto-discovery expects tests at root level

**fixtures/:**
- ✅ Test data files (JSON, CSV, sample files)
- ❌ NOT Python test files
- Purpose: Data loaded by tests

**mocks/:**
- ✅ Mock implementations of external services
- ✅ Python classes that fake APIs
- ❌ NOT actual test files
- Purpose: Imported by tests to avoid real API calls

### scripts/ vs tests/

**scripts/:**
- Utility scripts (init_db.py, backup_db.py)
- Demo scripts (demo_*.py, preview_*.py)
- NOT test files

**tests/:**
- Test files only (test_*.py)
- Supporting data (fixtures/, mocks/)

### Example Usage in Tests

```python
# In tests/test_tag_system.py
import json
from pathlib import Path

# Load fixture data
fixtures_dir = Path(__file__).parent / "fixtures"
with open(fixtures_dir / "sample_notes.json") as f:
    sample_data = json.load(f)

# Use mock for external service
from tests.mocks.mock_clockify import MockClockifyClient
clockify = MockClockifyClient()
```

### Test File Naming

**Pattern:** `test_<component_name>.py`

**Examples:**
- `test_tag_system.py` - Tests for tag_utils.py
- `test_database.py` - Tests for database connection
- `test_templates.py` - Tests for template engine
- `test_time_tracking.py` - Tests for time parsing

### Why This Structure?

**pytest Discovery:**
- pytest looks for test_*.py files in tests/ directory
- Subdirectories are for supporting files, not tests
- Standard Python testing convention

**Clarity:**
- Clear separation: tests vs data vs mocks
- Easy to find what you need
- Follows Python community standards

---

## TYPE HINTS

**Standard**: Use everywhere
```python
def validate_template(self, template: Dict[str, Any]) -> List[str]:
    """Validate a complete template."""
    ...
```

---

## DOCSTRINGS

**Standard**: Google-style for all public functions
```python
def create(
    self,
    content: str,
    tags: List[str],
    project_id: Optional[int] = None
) -> Note:
    """
    Create a new note.
    
    Args:
        content: Note content (clean text without hashtags)
        tags: List of full tag names (e.g., ['internal-only'])
        project_id: Optional project ID to link
        
    Returns:
        Created Note object
    """
```

---

## ERROR HANDLING

**Standard**: Try-finally for resource cleanup
```python
session = get_session()
try:
    # Database operations
    pass
finally:
    session.close()
```

---

## LESSONS LEARNED FROM PATTERN CORRECTIONS

### Mistake 1: Shortened Singleton Name
**Wrong**: `get_validator()`
**Right**: `get_template_validator()`
**Why**: Doesn't follow the descriptive naming pattern

### Mistake 2: Removed __init__.py Structure
**Wrong**: Minimal __init__.py with just imports
**Right**: Full docstring, __all__
**Why**: Package initialization files need documentation too

### Mistake 3: Inconsistent with Existing Code
**Wrong**: Breaking established patterns without discussion
**Right**: Follow existing patterns unless explicitly changing them
**Why**: Consistency is crucial for maintainability

### Mistake 4: Tests in Wrong Directory (20251226)
**Wrong**: test_*.py files in scripts/ directory
**Right**: test_*.py files in tests/ root directory
**Why**: pytest expects tests at root level; scripts/ is for utilities

### Mistake 5: Assumed Version Information (20251226)
**Wrong**: Putting version numbers in file-structure.md
**Right**: Versions in CHANGELOG.md and git tags only
**Why**: Single source of truth; avoids duplication

---

## SUMMARY OF STANDARDS

### File Organization
- ✅ CLI commands in workmain/cli/commands/
- ✅ Repositories in workmain/database/repositories/
- ✅ Utilities in workmain/utils/
- ✅ Tests in tests/ (root level)
- ✅ Test data in tests/fixtures/
- ✅ Mocks in tests/mocks/
- ✅ Scripts in scripts/ (utilities only)

### Version Tracking
- ✅ Git tags (release record)
- ✅ CHANGELOG.md (source of truth)
- ✅ __version__.py (project-level)
- ❌ NOT in file headers (module docstrings)
- ❌ NOT in file-structure.md
- ❌ NOT in implementation-checklist.md

### Naming Patterns
- ✅ Singleton: `get_<descriptive_name>()`
- ✅ Test files: `test_<component>.py`
- ✅ Demo scripts: `demo_<purpose>.py`
- ✅ Utility scripts: `<verb>_<noun>.py`

### Code Quality
- ✅ Type hints everywhere
- ✅ Google-style docstrings
- ✅ Try-finally for cleanup
- ✅ Repository pattern for database

---

**End of Development Standards Review v3.0**

**Changes in v3.0:**
- Retired the version-header / version-history file pattern (File Header Removal spec v1.3)
- File Header Pattern rewritten to the PEP 257 module-docstring shape
- Removed the old per-file version-history documentation pattern
- Package `__init__.py` Pattern: version-history docstring and `__version__` standard removed
- Import Organization example header trimmed to the PEP 257 shape
- FILE VERSIONING section removed
- VERSION TRACKING LOCATIONS rewritten: git tags, `CHANGELOG.md`, and `workmain/__version__.py`
  are the tracking locations; file headers dropped from the list
- Mistake 2 and Mistake 5 guidance corrected to match the retired practice
- SUMMARY sections realigned to the new standard

**Changes in v2.0:**
- Added version tracking locations section
- Added test organization standards
- Added lessons learned from Dec 26 session
- Clarified where versions ARE and are NOT tracked
- Added test file placement rules and examples

These standards ensure consistency, maintainability, and quality throughout the WorkmAIn project.

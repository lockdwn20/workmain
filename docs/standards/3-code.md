## 3. Code Standards

### 3.1 Module headers

- PEP 257 module docstring: a one-line summary, then a paragraph describing what the module does and why. **No version, no date, no version-history block** — git tags, `CHANGELOG.md`, and `workmain/__version__.py` are the version record. **No terminal command, no instruction to set an environment variable, no command-line flag, no terminal invocation, no trigger for when to run something, and no inventory of the module's own contents.** Naming an environment variable the module reads, or the API call that yields an instance of it, is a description of what the module requires and how it is obtained, and belongs here. A command belongs to `argparse` or to a Click command's own docstring (§5.6), which is where a reader looking for it will be.

  ```python
  """
  Parses, validates, converts and formats tags for display.

  Tags are case-insensitive, are normalized on entry, and are validated
  against config/tags.json. Callers receive full names; short forms are an
  input convenience and are never stored.
  """
  ```

- *NOTE: Duplicating version history in every file was retired in v1.29.0.*

### 3.2 Import organization

- Standard library, then third-party, then local — blank line between groups.

  ```python
  from datetime import date, datetime
  from typing import List, Optional

  from sqlalchemy import func, and_, or_
  from sqlalchemy.orm import Session

  from workmain.database.models import Note, Meeting, Project
  ```

### 3.3 Singletons

- Module-level `_<name>_instance = None`, created on first call, accessed through a **descriptive** getter.

  ```python
  _tag_system_instance = None

  def get_tag_system() -> TagSystem:
      """Get singleton instance of TagSystem."""
      global _tag_system_instance
      if _tag_system_instance is None:
          _tag_system_instance = TagSystem()
      return _tag_system_instance
  ```

| Correct | Wrong |
| --- | --- |
| `get_tag_system()` | `get_tags()` |
| `get_template_loader()` | `get_loader()` |
| `get_template_validator()` | `get_validator()` |
| `get_style_adapter()` | `get_adapter()` |

### 3.4 Package `__init__.py`

- A package that exposes an API gets a §3.1 docstring, imports of its classes *and* singleton getters, and an `__all__` declaring them. A package that exposes nothing — a namespace holding modules that callers import directly — gets the §3.1 docstring and nothing else. Which one a package is, is a fact about it: if no caller writes `from <package> import <name>`, it exposes nothing, and inventing exports to satisfy this section is not conformance. No `__version__` constant in either.

### 3.5 Function and class docstrings

- **This section governs functions and classes. It does not govern module headers, which are §3.1's.** Type hints on every parameter and return. Google-style docstrings on every public function and class — `Args:`, `Returns:`, `Raises:`, `Attributes:`. Those blocks belong to a function or a class and never appear in a module header.

  ```python
  def create(self, content: str, tags: List[str], project_id: Optional[int] = None) -> Note:
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

### 3.6 Integration over separation

- Enhance an existing command file when adding to an existing group.
- New files are only for approved distinct command groups.

### 3.7 Security

- Never commit secrets.
- All secrets are stored as KV pairs in the .env and utilized through python-dotenv
- Nothing encrypts secrets at rest; `.env` must be `chmod 600`.

### 3.8 Framework mechanisms first

- **Use the mechanism Python's standard library, Click, Rich or SQLAlchemy provides before writing your own.** Where two of them do the job, either meets this rule, unless another section names one.
- **A spec that writes its own records why.** Its Decision Log names the mechanism it set aside and the reason it does not fit.
- The library's version is tested and behaves the same in every caller. A hand-written version has to get every edge case right on its own, and each copy can get a different one wrong.

| Job | Written by hand | Use instead |
| --- | --- | --- |
| Ask for a number from 1 to `n` | A loop that converts and bounds-checks the input. One that rejects only `0` and values above `n` accepts `-1`, which Python reads as an index from the end of the list. | `click.prompt(..., type=click.IntRange(1, n))` |
| Restrict an option to fixed values | An `if value not in (...)` check in the command body | `type=click.Choice([...])` on the option |
| Parse a `YYYY-MM-DD` date | Splitting on `-` and building a `date` from the parts | `date.fromisoformat(value)` |
| Build a file path | Joining strings with `/` | `pathlib.Path(base) / name` |

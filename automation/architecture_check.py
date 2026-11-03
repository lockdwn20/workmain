"""
Checks the code against docs/ARCHITECTURE.md and reports every mismatch.

The map is the standard: this module reads the map and the source, and edits
neither. Every path it checks against comes from the map — the layers and
their packages from map section 1's table, the owned modules from map section 2's lines, and the
code each known deficiency covers from the "Covers" sentence of its map section 3 entry.
A mismatch inside code a map section 3 entry covers is reported as that known deficiency
and does not fail the run; any other mismatch is new and fails it, to be fixed
in the code or brought to Ray as a change to the map. Asking whether a map section 3
entry's issues are still open needs the GitHub CLI, `gh`.

Exit 0 when nothing new is found, 1 otherwise.
"""

import argparse
import ast
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Pattern, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
MAP_PATH = ROOT / "docs" / "ARCHITECTURE.md"
PACKAGE = "workmain"

Layer = Tuple[str, List[Tuple[str, Pattern]]]
Entry = Tuple[str, List[int], List[Pattern]]
Finding = Tuple[str, str]


# ---------------------------------------------------------------- the map

def _sections(text: str) -> Dict[str, List[str]]:
    """Split the map into its '## ' sections, keyed by heading."""
    out: Dict[str, List[str]] = {}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            out[current] = []
        elif current is not None:
            out[current].append(line)
    return out


def _section(sections: Dict[str, List[str]], number: int) -> List[str]:
    """The lines of the section whose heading starts with `number`."""
    for heading, lines in sections.items():
        if heading.startswith(f"{number}."):
            return lines
    raise SystemExit(f"{MAP_PATH.relative_to(ROOT)} has no section {number}")


def _code_paths(text: str) -> List[str]:
    """Backtick-quoted paths under the package, in order."""
    return [p for p in re.findall(r"`([^`]+)`", text) if p.startswith(PACKAGE + "/")]


def _pattern(path: str) -> Pattern:
    """A map path as a regex over repository-relative file paths.

    A path ending in '/' covers everything under it. '<name>' matches one path
    segment, and '**/' any number of them, none included.
    """
    rx = re.escape(path)
    rx = rx.replace(re.escape("**") + "/", "(?:.*/)?")
    rx = re.sub(re.escape("<") + r"[^>]+" + re.escape(">"), "[^/]+", rx)
    return re.compile("^" + rx + (".*" if path.endswith("/") else "$"))


def read_layers(sections: Dict[str, List[str]]) -> List[Layer]:
    """
    Read the layers from map section 1's table.

    Args:
        sections: The map, split by `_sections`.

    Returns:
        One (layer name, [(path, pattern)]) pair per table row, top layer first.

    Raises:
        SystemExit: map section 1 has no layer table.
    """
    layers = []
    for line in _section(sections, 1):
        m = re.match(r"\|\s*\*\*(\w+)\*\*\s*\|(.*?)\|", line)
        if m:
            layers.append((m.group(1), [(p, _pattern(p)) for p in _code_paths(m.group(2))]))
    if not layers:
        raise SystemExit("map section 1 has no layer table")
    return layers


def read_owned(sections: Dict[str, List[str]]) -> List[Tuple[str, Pattern]]:
    """
    Read the owned modules from map section 2's lines.

    Args:
        sections: The map, split by `_sections`.

    Returns:
        A (path, pattern) pair for every package path named before a line's " — ".
    """
    return [(p, _pattern(p)) for line in _section(sections, 2) if line.startswith("- ")
            for p in _code_paths(line.split(" — ")[0])]


def read_deficiencies(sections: Dict[str, List[str]]) -> List[Entry]:
    """
    Read the known deficiencies from map section 3's entries.

    An entry is a paragraph that opens with a bold title. Its issues are the
    numbers in its title, and the code it covers is the package paths in its
    "Covers" sentence; paths anywhere else in the entry cover nothing.

    Args:
        sections: The map, split by `_sections`.

    Returns:
        One (title, issue numbers, cover patterns) triple per entry, in map order.
    """
    entries = []
    for line in _section(sections, 3):
        m = re.match(r"\*\*(.+?)\*\*\s*(.*)", line)
        if not m:
            continue
        title, rest = m.group(1).rstrip("."), m.group(2)
        covers = re.match(r"Covers ((?:`[^`]*`|[^.`])*)\.", rest)
        patterns = [_pattern(p) for p in _code_paths(covers.group(1))] if covers else []
        entries.append((title, [int(n) for n in re.findall(r"#(\d+)", title)], patterns))
    return entries


# ---------------------------------------------------------------- the code

def modules() -> Dict[str, ast.Module]:
    """
    Parse every Python file under the package.

    Returns:
        Each file's syntax tree, keyed by its repository-relative path.
    """
    out = {}
    for path in sorted((ROOT / PACKAGE).rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(ROOT).as_posix()
        out[rel] = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
    return out


def _dotted_to_path(dotted: str, known: Dict[str, ast.Module]) -> Optional[str]:
    """The known module file a dotted name refers to, or None."""
    base = dotted.replace(".", "/")
    for candidate in (base + ".py", base + "/__init__.py"):
        if candidate in known:
            return candidate
    return None


def _module_dotted(rel: str) -> str:
    """A repository-relative module path as its dotted name."""
    parts = rel[:-3].split("/")
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def imports(rel: str, tree: ast.Module, known: Dict[str, ast.Module]) -> List[Tuple[int, str]]:
    """
    Find every import of a package module, including imports inside functions.

    `from package import name` resolves to the submodule `name` when there is
    one, and to the package otherwise.

    Args:
        rel: The importing module's repository-relative path.
        tree: That module's syntax tree.
        known: Every package module, keyed by path, as `modules` returns.

    Returns:
        Distinct (line number, imported module path) pairs, sorted.
    """
    here = _module_dotted(rel)
    is_pkg = rel.endswith("__init__.py")
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(PACKAGE):
                    target = _dotted_to_path(alias.name, known)
                    if target:
                        found.add((node.lineno, target))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = here.split(".")
                base = base[: len(base) - node.level + (1 if is_pkg else 0)]
                dotted = ".".join(base + ([node.module] if node.module else []))
            else:
                dotted = node.module or ""
            if not dotted.startswith(PACKAGE):
                continue
            for alias in node.names:
                target = _dotted_to_path(f"{dotted}.{alias.name}", known) or _dotted_to_path(dotted, known)
                if target:
                    found.add((node.lineno, target))
    return sorted(found)


def layer_of(rel: str, layers: List[Layer]) -> Tuple[Optional[int], Optional[str]]:
    """
    Find the layer a module belongs to.

    Args:
        rel: The module's repository-relative path.
        layers: The layers, as `read_layers` returns them.

    Returns:
        The (index, name) of the layer whose longest matching path covers the
        module, or (None, None) when none does.
    """
    best = None
    for index, (name, patterns) in enumerate(layers):
        for path, rx in patterns:
            if rx.match(rel) and (best is None or len(path) > best[0]):
                best = (len(path), index, name)
    return (best[1], best[2]) if best else (None, None)


# ---------------------------------------------------------------- the checks

def check_layers(mods: Dict[str, ast.Module], layers: List[Layer]) -> List[Finding]:
    """
    Find imports that break map section 1's layer rules.

    An import is a finding when it points to a higher layer, when a surface
    reaches data other than `database/connection.py`, or when a capability
    imports anything from the data layer.

    Args:
        mods: Every package module, as `modules` returns.
        layers: The layers, as `read_layers` returns them.

    Returns:
        One (importing module path, description) pair per finding.
    """
    out = []
    for rel, tree in mods.items():
        src_i, src = layer_of(rel, layers)
        if src_i is None:
            continue
        for line, target in imports(rel, tree, mods):
            dst_i, dst = layer_of(target, layers)
            if dst_i is None or target == rel:
                continue
            if dst_i < src_i:
                out.append((rel, f"{rel}:{line} — {src} imports {dst} (upward): {target}"))
            elif src == "Surfaces" and dst == "Data" and not target.endswith("database/connection.py"):
                out.append((rel, f"{rel}:{line} — a surface reaches data directly: {target}"))
            elif src == "Capabilities" and dst == "Data":
                out.append((rel, f"{rel}:{line} — a capability imports from the database: {target}"))
    return out


def check_duplicates(mods: Dict[str, ast.Module]) -> List[Finding]:
    """
    Find public class names defined in more than one module (map section 1, Result types).

    Function names may repeat, because a function is always called through its
    module.

    Args:
        mods: Every package module, as `modules` returns.

    Returns:
        One (first defining module path, description) pair per repeated name.
    """
    where: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
    for rel, tree in mods.items():
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                where[node.name].append((rel, node.lineno))
    return [(sites[0][0], f"class {name} is defined {len(sites)} times: "
             + ", ".join(f"{r}:{n}" for r, n in sites))
            for name, sites in sorted(where.items()) if len(sites) > 1]


def check_ownership(mods: Dict[str, ast.Module], owned: List[Tuple[str, Pattern]]) -> List[Finding]:
    """
    Find modules no map section 2 line gives an owner. `__init__.py` files are left to `check_packages`.

    Args:
        mods: Every package module, as `modules` returns.
        owned: The owned paths, as `read_owned` returns them.

    Returns:
        One (module path, description) pair per unowned module.
    """
    return [(rel, f"{rel} — no owner in map section 2") for rel in mods
            if not rel.endswith("__init__.py") and not any(rx.match(rel) for _, rx in owned)]


def check_packages(mods: Dict[str, ast.Module]) -> List[Finding]:
    """
    Find `__init__.py` files that break map section 1's Packages rule.

    A finding is an `__init__.py` with no docstring, one holding anything after
    its docstring, or one with no Python module beside it.

    Args:
        mods: Every package module, as `modules` returns.

    Returns:
        One (`__init__.py` path, description) pair per finding.
    """
    out = []
    for rel, tree in mods.items():
        if not rel.endswith("__init__.py"):
            continue
        body = tree.body
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            body = body[1:]
        else:
            out.append((rel, f"{rel} — has no docstring"))
        if body:
            out.append((rel, f"{rel}:{body[0].lineno} — holds {len(body)} statement(s) besides its docstring"))
        pkg = Path(rel).parent
        siblings = [m for m in mods if Path(m).parent == pkg and m != rel]
        subpackages = [m for m in mods if Path(m).parent.parent == pkg and m.endswith("__init__.py")]
        if not siblings and not subpackages:
            has_files = any(p.is_file() and p.suffix != ".py" for p in (ROOT / pkg).iterdir())
            out.append((rel, f"{rel} — makes a package of a folder that holds no Python module" if has_files
                        else f"{rel} — a package with no modules"))
    return out


def check_issues(entries: List[Entry], ask_github: bool) -> Tuple[List[str], List[str]]:
    """
    Check map section 3's entries against their issues.

    Args:
        entries: The known deficiencies, as `read_deficiencies` returns them.
        ask_github: Whether to ask `gh` for each named issue's state.

    Returns:
        The titles of entries that name no issue, and a description of each
        entry whose named issues are all closed or could not be read.
    """
    awaiting, closed = [], []
    for title, numbers, _ in entries:
        if not numbers:
            awaiting.append(title)
            continue
        if not ask_github:
            continue
        states = {}
        for n in numbers:
            result = subprocess.run(["gh", "issue", "view", str(n), "--json", "state"],
                                    capture_output=True, text=True, cwd=ROOT)
            if result.returncode != 0:
                closed.append(f"'{title}': could not read #{n} ({result.stderr.strip()})")
                continue
            states[n] = json.loads(result.stdout)["state"]
        if states and all(s == "CLOSED" for s in states.values()):
            closed.append(f"'{title}': every issue it names is closed — remove the entry and enforce the rule")
    return awaiting, closed


# ---------------------------------------------------------------- main

def main(argv: Optional[Sequence[str]] = None) -> int:
    """
    Run every check and print the report.

    Args:
        argv: Command-line arguments; the process's own when None.

    Returns:
        0 when nothing new is found and no map section 3 entry needs removing, 1 otherwise.
    """
    parser = argparse.ArgumentParser(description="Check the code against docs/ARCHITECTURE.md.")
    parser.add_argument("--check-issues", action="store_true",
                        help="ask gh whether each map section 3 entry's issues are still open")
    args = parser.parse_args(argv)

    sections = _sections(MAP_PATH.read_text(encoding="utf-8"))
    layers = read_layers(sections)
    entries = read_deficiencies(sections)
    mods = modules()

    findings = (check_layers(mods, layers) + check_duplicates(mods)
                + check_ownership(mods, read_owned(sections)) + check_packages(mods))

    known: Dict[str, List[str]] = defaultdict(list)
    new: List[str] = []
    for path, text in findings:
        entry = next((e for e in entries if any(rx.match(path) for rx in e[2])), None)
        if entry:
            known[entry[0]].append(text)
        else:
            new.append(text)

    print(f"Layers, top to bottom (from map section 1): {' > '.join(name for name, _ in layers)}")

    print(f"\nNew findings: {len(new)}")
    for text in new:
        print(f"  {text}")

    print(f"\nKnown deficiencies (map section 3): {sum(len(v) for v in known.values())} finding(s)")
    for title, _, _ in entries:
        if known[title]:
            print(f"  {title}: {len(known[title])}")

    awaiting, closed = check_issues(entries, args.check_issues)
    if awaiting:
        print(f"\nMap section 3 entries awaiting an issue: {len(awaiting)}")
        for title in awaiting:
            print(f"  {title}")
    if closed:
        print(f"\nMap section 3 entries to review: {len(closed)}")
        for text in closed:
            print(f"  {text}")
    if not args.check_issues:
        print("\n(map section 3 issue states not checked)")

    failed = bool(new or closed)
    print(f"\n{'FAIL' if failed else 'PASS'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

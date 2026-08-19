"""
Verify that the four places recording a release agree with each other.

Checks, for every `vN.N.N` tag on the repository:

  1. `CHANGELOG.md` has a matching `## [N.N.N]` section
  2. that section is non-empty (a heading with no body is a silent loss)
  3. a GitHub Release object exists for the tag

and, for `workmain/__version__.py`:

  4. `__version__` and `__version_info__` agree with each other
  5. `__version__` is not behind the newest tag (a stale version file)
  6. if `__version__` is ahead of every tag — a release in flight — CHANGELOG.md
     already carries its section, per §2.5's "update both together"

Exits non-zero on any mismatch at or above BASELINE, so it can gate a push to `main`.
Older releases are reported as accepted history and never fail the run.

    python3 automation/check_release_integrity.py             # full check
    python3 automation/check_release_integrity.py --no-remote # skip the gh Release check
    python3 automation/check_release_integrity.py --show-historical

Why this exists: `DEVELOPMENT_STANDARDS.md` §2.2 already requires a CHANGELOG entry
and a GitHub Release on every merge to `main`. The prose rule did not prevent four
tags shipping without a Release, nor a release-prep edit silently absorbing the
v1.28.0 section into v1.29.0's by replacing its heading. A rule that cannot fail
is not enforcement.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise SystemExit(f"could not find a repository root above {start}")


ROOT = find_repo_root(Path(__file__))
CHANGELOG = ROOT / "CHANGELOG.md"
VERSION_FILE = ROOT / "workmain" / "__version__.py"

# Releases at or above this version are enforced. Below it is accepted history:
# tagging predates the CHANGELOG's earliest sections, and the GitHub Release rule
# only entered DEVELOPMENT_STANDARDS §2.2 at v1.26.0. Pre-baseline gaps are counted
# and reported, never failed — a check that is permanently red gets ignored, which
# is how the rule it replaces failed in the first place.
#
# Raise this only when everything above the new floor is genuinely clean.
BASELINE = "1.26.0"


def sh(*args):
    r = subprocess.run(args, capture_output=True, text=True, cwd=ROOT)
    return r.stdout.strip() if r.returncode == 0 else ""


def version_key(v):
    return tuple(int(x) for x in v.split("."))


def changelog_sections(text):
    """Map version -> body line count, from `## [x.y.z]` headings."""
    heads = [(m.group(1), m.start()) for m in
             re.finditer(r"^## \[(\d+\.\d+\.\d+)\][^\n]*$", text, re.M)]
    out = {}
    for i, (ver, pos) in enumerate(heads):
        end = heads[i + 1][1] if i + 1 < len(heads) else len(text)
        body = text[text.index("\n", pos) + 1:end].strip()
        out[ver] = len(body.splitlines())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-remote", action="store_true",
                    help="skip the GitHub Release check (offline / no gh auth)")
    ap.add_argument("--show-historical", action="store_true",
                    help="list accepted pre-baseline gaps instead of just counting them")
    a = ap.parse_args()

    tags = sorted({t[1:] for t in sh("git", "tag").splitlines()
                   if re.fullmatch(r"v\d+\.\d+\.\d+", t)}, key=version_key)
    if not tags:
        print("no vN.N.N tags found — nothing to check")
        return 0

    sections = changelog_sections(CHANGELOG.read_text(encoding="utf-8"))
    releases = set()
    if not a.no_remote:
        releases = {ln.split()[0].lstrip("v") for ln in
                    sh("gh", "release", "list", "--limit", "200").splitlines() if ln.strip()}

    problems = []
    historical = []
    floor = version_key(BASELINE)

    def note(v, msg):
        (problems if version_key(v) >= floor else historical).append(f"v{v}: {msg}")

    vtext = VERSION_FILE.read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*["\'](\d+\.\d+\.\d+)["\']', vtext)
    mi = re.search(r'__version_info__\s*=\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', vtext)

    # The version currently being prepared: bumped in __version__.py, ahead of every
    # tag, not yet tagged. Its CHANGELOG section legitimately has no tag yet.
    in_flight = None
    if m and version_key(m.group(1)) > version_key(tags[-1]):
        in_flight = m.group(1)

    for v in tags:
        if v not in sections:
            note(v, f"tagged, but no `## [{v}]` section in CHANGELOG.md")
        elif sections[v] == 0:
            note(v, "CHANGELOG section exists but is empty")
        if not a.no_remote and v not in releases:
            note(v, f"tagged, but no GitHub Release "
                    f"(gh release create v{v} --generate-notes)")

    for v in sections:
        if v not in tags and v != in_flight:
            note(v, "CHANGELOG section with no matching git tag")

    if not m:
        problems.append("could not parse __version__ from workmain/__version__.py")
    else:
        ver = m.group(1)

        # __version_info__ is the same fact stored twice in one file — check it agrees.
        if not mi:
            problems.append("could not parse __version_info__ from workmain/__version__.py")
        elif ".".join(mi.groups()) != ver:
            problems.append(
                f"__version__.py disagrees with itself: __version__ is {ver} but "
                f"__version_info__ is ({', '.join(mi.groups())})")

        if version_key(ver) < version_key(tags[-1]):
            problems.append(
                f"__version__.py is {ver} but a newer tag v{tags[-1]} exists — "
                f"the version file is stale")
        elif version_key(ver) > version_key(tags[-1]):
            # A bump ahead of the newest tag is a release in flight, which is fine —
            # but §2.5 requires the version file and CHANGELOG move together, so the
            # entry must already exist. Catches "bumped, forgot the CHANGELOG" at the
            # point of the bump rather than after the tag is pushed.
            if ver not in sections:
                problems.append(
                    f"__version__.py is {ver} (ahead of tag v{tags[-1]}, a release in "
                    f"flight) but CHANGELOG.md has no `## [{ver}]` section — "
                    f"DEVELOPMENT_STANDARDS.md §2.5 requires both move together")

    scope = "tags vs CHANGELOG" if a.no_remote else "tags vs CHANGELOG vs Releases"
    enforced = [v for v in tags if version_key(v) >= floor]

    if problems:
        print(f"FAIL — {len(problems)} problem(s) at or above the v{BASELINE} "
              f"baseline [{scope}]\n")
        for p in problems:
            print(f"  - {p}")
    else:
        cur = m.group(1) if m else "?"
        flight = " (release in flight, untagged)" if in_flight else ""
        print(f"OK — {len(enforced)} release(s) at or above the v{BASELINE} baseline "
              f"are consistent [{scope}]; __version__.py = {cur}{flight}")

    if historical:
        print(f"\n{len(historical)} pre-baseline item(s) accepted as history "
              f"(not failed). Run with --show-historical to list them.")
        if a.show_historical:
            for h in historical:
                print(f"  - {h}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

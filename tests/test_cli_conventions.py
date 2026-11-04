"""
Tests that every command follows the CLI naming conventions.

docs/standards/5-cli.md §5.3 states which names a subcommand may use, and
§5.5 that a short flag means one long flag everywhere. These tests read the
command tree Click builds, so no command can drift from either without the
suite failing. The standard verbs are read from §5.3's own table; the approved
verbs, the existing exceptions and the flags with no short form are listed
here, and this file is their one home.
"""

import re
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set, Tuple

import click

from workmain.cli.interface import cli

STANDARDS = Path(__file__).resolve().parent.parent / "docs" / "standards" / "5-cli.md"

# Domain verbs Ray approved, each with its reason (§5.3). A verb is added only with his approval.
APPROVED_VERBS: Dict[str, str] = {
    "condense": "AI summarization",
    "rename": "rename without a full edit",
    "merge": "combine two records",
    "track": "a time entry from a meeting; a subcommand verb, never a group name",
    "log": "bulk multi-note editor workflow, distinct from add",
    "register": "template lifecycle",
    "unregister": "template lifecycle",
    "validate": "template schema validation",
    "complete": "lifecycle closure; edit does not imply finality",
    "dismiss": "deliberate non-completion",
    "confirm": "attestation without modification",
    "correct": "targeted correction with an audit trail; a distinct write target",
    "post": "Slack publishes to a channel rather than sending to a recipient",
}

# Top-level commands §5.1 permits, as workflows that coordinate several groups.
TOP_LEVEL = {"eod", "status", "today"}

# Subgroups whose commands are named for what they act on (§5.2). None means any name.
NOUN_SUBGROUPS: Dict[str, Optional[Set[str]]] = {
    "set": None,
    "upload": None,
    "sync": {"push", "pull", "both"},
}

# Commands that existed before this test and follow none of the rules above. This
# list only shrinks: an entry leaves when its command is renamed or removed, and
# nothing is added. A new name is a standard verb, or an approved one.
EXISTING_EXCEPTIONS = {
    "calendar month", "calendar sync", "calendar today", "calendar week",
    "email assign", "email unassign",
    "init",
    "meetings costs", "meetings reschedule", "meetings skip", "meetings template use", "meetings today", "meetings upcoming",
    "notes costs", "notes date", "notes meeting", "notes search", "notes today",
    "notifications disable", "notifications enable", "notifications set", "notifications test",
    "providers costs", "providers test",
    "reports corrections", "reports costs", "reports history", "reports resend",
    "slack setup",
    "tasks today",
    "time date", "time today", "time week",
}

# Long flags that have no short form on purpose (§5.5).
NO_SHORT_FORM = {
    "--dry-run", "--force", "--send", "--preview", "--recurring",
    "--include-weekends", "--cancelled", "--status", "--all", "--fallback",
}


def standard_verbs() -> Set[str]:
    """
    Read the standard verbs from §5.3's table in docs/standards/5-cli.md.

    Returns:
        The verb in the second column of each row of the table.
    """
    section = STANDARDS.read_text(encoding="utf-8").split("### 5.3")[1].split("### 5.4")[0]
    return set(re.findall(r"^\| [^|`]+ \| `([a-z]+)` \|", section, re.MULTILINE))


def walk(group: click.Group, path: Tuple[str, ...] = ()) -> Iterator[Tuple[Tuple[str, ...], click.Command]]:
    """
    Yield every command under a group, depth first, with its full path.

    Args:
        group: The group to walk.
        path: The names leading to `group`.

    Returns:
        An iterator of (path of names, command) pairs, groups included.
    """
    for name, command in sorted(group.commands.items()):
        yield path + (name,), command
        if isinstance(command, click.Group):
            yield from walk(command, path + (name,))


def commands() -> List[Tuple[Tuple[str, ...], click.Command]]:
    """
    List every command that runs something, groups excluded.

    Returns:
        (path of names, command) pairs for every leaf command.
    """
    return [(path, cmd) for path, cmd in walk(cli) if not isinstance(cmd, click.Group)]


def name_is_allowed(path: Tuple[str, ...]) -> bool:
    """
    Decide whether a command's name follows §5.1–§5.3, before exceptions.

    Args:
        path: The command's full path of names.

    Returns:
        True when the name is a permitted top-level command, a noun under a
        subgroup that takes nouns, a standard verb, or an approved verb.
    """
    name = path[-1]
    if len(path) == 1:
        return name in TOP_LEVEL
    parent = path[-2]
    if parent in NOUN_SUBGROUPS:
        allowed = NOUN_SUBGROUPS[parent]
        return allowed is None or name in allowed
    return name in standard_verbs() or name in APPROVED_VERBS


def options() -> Iterator[Tuple[str, click.Option]]:
    """
    Yield every option on every command and group.

    Returns:
        An iterator of (command path, option) pairs.
    """
    for path, command in [((), cli)] + list(walk(cli)):
        for param in command.params:
            if isinstance(param, click.Option):
                yield " ".join(path) or "workmain", param


def long_name(option: click.Option) -> str:
    """The option's first long form, such as `--limit`, or its first name when it has none."""
    names = option.opts + option.secondary_opts
    return next((o for o in names if o.startswith("--")), names[0])


def short_names(option: click.Option) -> List[str]:
    """The option's short forms, such as `-n`."""
    return [o for o in option.opts + option.secondary_opts if not o.startswith("--")]


class TestCommandNames:

    def test_every_row_of_the_5_3_table_yields_a_verb(self) -> None:
        section = STANDARDS.read_text(encoding="utf-8").split("### 5.3")[1].split("### 5.4")[0]
        table = section.split("| Action | Verb | Do not use |")[1].split("\n\n")[0]
        rows = [line for line in table.splitlines() if line.startswith("| ") and "---" not in line]
        assert len(rows) > 0
        assert len(standard_verbs()) == len(rows)

    def test_every_command_has_an_approved_name(self) -> None:
        offenders = [" ".join(path) for path, _ in commands()
                     if not name_is_allowed(path) and " ".join(path) not in EXISTING_EXCEPTIONS]
        assert offenders == []

    def test_every_existing_exception_is_still_in_use(self) -> None:
        in_use = {" ".join(path) for path, _ in commands()}
        assert sorted(EXISTING_EXCEPTIONS - in_use) == []

    def test_no_existing_exception_is_now_allowed(self) -> None:
        allowed = {" ".join(path) for path, _ in commands() if name_is_allowed(path)}
        assert sorted(EXISTING_EXCEPTIONS & allowed) == []


class TestShortFlags:

    def test_each_short_flag_means_one_long_flag_everywhere(self) -> None:
        meanings: Dict[str, Set[str]] = {}
        for _, option in options():
            for short in short_names(option):
                meanings.setdefault(short, set()).add(long_name(option))
        assert {short: sorted(longs) for short, longs in meanings.items() if len(longs) > 1} == {}

    def test_flags_kept_without_a_short_form_have_none(self) -> None:
        offenders = [f"{where} {long_name(option)} {short_names(option)}" for where, option in options()
                     if long_name(option) in NO_SHORT_FORM and short_names(option)]
        assert offenders == []

    def test_minus_h_is_never_reassigned(self) -> None:
        offenders = [f"{where} {long_name(option)}" for where, option in options()
                     if "-h" in short_names(option) and long_name(option) != "--help"]
        assert offenders == []

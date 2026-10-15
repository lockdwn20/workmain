"""
Tests for workmain.cli.params: the date and picker parameter types.
"""

from datetime import date, timedelta

import click
import pytest
from click.testing import CliRunner

from workmain.cli.params import DateParamType, PickParamType


class TestDateParamType:
    def test_convert_words_and_iso(self):
        t = DateParamType()
        assert t.convert("today", None, None) == date.today()
        assert t.convert("yesterday", None, None) == date.today() - timedelta(days=1)
        assert t.convert("2099-01-01", None, None) == date(2099, 1, 1)

    def test_bad_date_is_a_usage_error(self):
        @click.command()
        @click.option("--d", type=DateParamType())
        def cmd(d):
            pass

        result = CliRunner(mix_stderr=False).invoke(cmd, ["--d", "notadate"])
        assert result.exit_code == 2
        assert "Error:" in result.stderr


class TestPickParamType:
    def test_q_cancels_and_numbers_convert(self):
        t = PickParamType(3)
        assert isinstance(t, click.IntRange)
        assert t.convert("q", None, None) is None
        assert t.convert("Q", None, None) is None
        assert t.convert("2", None, None) == 2

    def test_out_of_range_and_text_are_rejected(self):
        t = PickParamType(3)
        for text in ("0", "-1", "4", "x"):
            with pytest.raises(click.BadParameter):
                t.convert(text, None, None)
        with pytest.raises(click.BadParameter) as exc:
            t.convert("x", None, None)
        assert "'x' is not a valid choice." in str(exc.value.message)

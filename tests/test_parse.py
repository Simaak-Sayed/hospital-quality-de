"""Tests for the DESTATIS workbook parser."""

from __future__ import annotations

from hospital_quality.parse import parse_value


class TestParseValue:
    def test_plain_integer(self) -> None:
        assert parse_value(2411) == (2411.0, None)

    def test_float_passthrough(self) -> None:
        assert parse_value(7.2) == (7.2, None)

    def test_german_decimal_comma(self) -> None:
        value, flag = parse_value("14,01")
        assert value == 14.01
        assert flag is None

    def test_german_thousands_separator(self) -> None:
        value, flag = parse_value("665.565")
        assert value == 665565.0
        assert flag is None

    def test_nil_marker_is_flagged_not_zero(self) -> None:
        # The crucial invariant: a placeholder must not become 0.0, which would
        # corrupt averages.
        assert parse_value("-") == (None, "nil")

    def test_unknown_marker(self) -> None:
        assert parse_value(".") == (None, "unknown")

    def test_blank_is_missing(self) -> None:
        assert parse_value("") == (None, "missing")
        assert parse_value(None) == (None, "missing")

    def test_unparseable_text(self) -> None:
        assert parse_value("n/a") == (None, "unparsed")

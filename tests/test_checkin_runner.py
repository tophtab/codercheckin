import pytest

from checkin_runner import parse_targets


def test_parse_targets_uses_default_targets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CHECKIN_TARGETS", raising=False)

    assert parse_targets() == ["nodeseek", "deepflood", "v2ex"]


def test_parse_targets_rejects_unknown_target(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHECKIN_TARGETS", "nodeseek,unknown")

    with pytest.raises(ValueError, match="Unknown check-in targets"):
        parse_targets()

"""SingleTapeTM motoru için birim testleri."""
from __future__ import annotations

from pathlib import Path

import pytest

from turinglab import SingleTapeTM, Tape


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _write_yaml(tmp_path: Path, text: str, name: str = "tm.yaml") -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


@pytest.mark.parametrize(
    "input_string, expected",
    [
        ("0", "1"),
        ("1", "10"),
        ("1011", "1100"),
        ("111", "1000"),
        ("11111111", "100000000"),
    ],
)
def test_binary_increment(input_string: str, expected: str) -> None:
    tm = SingleTapeTM.from_yaml(FIXTURES_DIR / "binary_increment.yaml")
    r = tm.run(input_string, max_steps=2000)
    assert r.accepted is True
    assert r.reason == "accept"
    assert r.final_tape.strip("B") == expected


@pytest.mark.parametrize(
    "input_string, expected",
    [
        ("", "1"),
        ("1", "11"),
        ("11", "111"),
        ("111", "1111"),
        ("11111", "111111"),
    ],
)
def test_unary_increment(input_string: str, expected: str) -> None:
    tm = SingleTapeTM.from_yaml(FIXTURES_DIR / "unary_increment.yaml")
    r = tm.run(input_string, max_steps=200)
    assert r.accepted is True
    assert r.reason == "accept"
    assert r.final_tape.strip("B") == expected


@pytest.mark.parametrize(
    "input_string, expected_acc",
    [
        ("", True),
        ("a", False),
        ("aa", True),
        ("aaa", False),
        ("aaaaaa", True),
    ],
)
def test_even_a(input_string: str, expected_acc: bool) -> None:
    tm = SingleTapeTM.from_yaml(FIXTURES_DIR / "even_a.yaml")
    r = tm.run(input_string, max_steps=200)
    assert r.accepted is expected_acc


def test_history_length_matches_steps() -> None:
    tm = SingleTapeTM.from_yaml(FIXTURES_DIR / "binary_increment.yaml")
    r = tm.run("1011", max_steps=2000)
    assert len(r.history) == r.steps + 1
    assert r.history[0].step == 0
    assert r.history[0].state == tm.start_state
    assert r.history[0].head_position == 0


def test_history_records_step_progression() -> None:
    tm = SingleTapeTM.from_yaml(FIXTURES_DIR / "unary_increment.yaml")
    r = tm.run("111", max_steps=100)
    for i, cfg in enumerate(r.history):
        assert cfg.step == i
    assert r.history[-1].state in tm.accept_states


def test_timeout(tmp_path: Path) -> None:
    yaml_text = """
name: spinner
states: [q0]
input_alphabet: ["1"]
tape_alphabet: ["1", "B"]
blank: B
start_state: q0
accept_states: []
transitions:
  - {state: q0, read: "1", next: q0, write: "1", move: R}
  - {state: q0, read: "B", next: q0, write: "B", move: L}
"""
    tm = SingleTapeTM.from_yaml(_write_yaml(tmp_path, yaml_text))
    r = tm.run("1", max_steps=50)
    assert r.accepted is False
    assert r.reason == "timeout"
    assert r.steps == 50


def test_no_transition(tmp_path: Path) -> None:
    yaml_text = """
name: stuck
states: [q0]
input_alphabet: ["0", "1"]
tape_alphabet: ["0", "1", "B"]
blank: B
start_state: q0
accept_states: []
transitions:
  - {state: q0, read: "1", next: q0, write: "1", move: R}
"""
    tm = SingleTapeTM.from_yaml(_write_yaml(tmp_path, yaml_text))
    r = tm.run("110", max_steps=100)
    assert r.accepted is False
    assert r.reason == "no_transition"
    assert r.steps == 2


def test_accept_at_start(tmp_path: Path) -> None:
    yaml_text = """
name: trivial
states: [q_acc]
input_alphabet: ["1"]
tape_alphabet: ["1", "B"]
blank: B
start_state: q_acc
accept_states: [q_acc]
transitions: []
"""
    tm = SingleTapeTM.from_yaml(_write_yaml(tmp_path, yaml_text))
    r = tm.run("1", max_steps=10)
    assert r.accepted is True
    assert r.reason == "accept"
    assert r.steps == 0
    assert len(r.history) == 1


def test_verbose_format(capsys) -> None:
    tm = SingleTapeTM.from_yaml(FIXTURES_DIR / "unary_increment.yaml")
    tm.run("1", max_steps=20, verbose=True)
    out = capsys.readouterr().out
    lines = [ln for ln in out.splitlines() if ln.strip()]
    assert len(lines) >= 2
    assert lines[0].startswith("Adım 0 |")
    for ln in lines:
        assert "[" in ln and "]" in ln
        assert "Durum:" in ln
        assert "Şerit:" in ln
    assert "(durdu:" in lines[-1]


def test_yaml_missing_field(tmp_path: Path) -> None:
    yaml_text = """
states: [q0]
input_alphabet: ["1"]
tape_alphabet: ["1", "B"]
blank: B
start_state: q0
"""
    p = _write_yaml(tmp_path, yaml_text, "missing.yaml")
    with pytest.raises(ValueError, match="eksik alanlar"):
        SingleTapeTM.from_yaml(p)


def test_yaml_invalid_move(tmp_path: Path) -> None:
    yaml_text = """
name: bad_move
states: [q0]
input_alphabet: ["1"]
tape_alphabet: ["1", "B"]
blank: B
start_state: q0
accept_states: []
transitions:
  - {state: q0, read: "1", next: q0, write: "1", move: X}
"""
    p = _write_yaml(tmp_path, yaml_text, "bad_move.yaml")
    with pytest.raises(ValueError, match="hareket yönü"):
        SingleTapeTM.from_yaml(p)


def test_yaml_duplicate_transition(tmp_path: Path) -> None:
    yaml_text = """
name: dup
states: [q0]
input_alphabet: ["1"]
tape_alphabet: ["1", "B"]
blank: B
start_state: q0
accept_states: []
transitions:
  - {state: q0, read: "1", next: q0, write: "1", move: R}
  - {state: q0, read: "1", next: q0, write: "0", move: L}
"""
    p = _write_yaml(tmp_path, yaml_text, "dup.yaml")
    with pytest.raises(ValueError, match="Çift δ kuralı"):
        SingleTapeTM.from_yaml(p)


def test_yaml_unknown_start_state(tmp_path: Path) -> None:
    yaml_text = """
name: bad_start
states: [q0]
input_alphabet: ["1"]
tape_alphabet: ["1", "B"]
blank: B
start_state: qZ
accept_states: []
transitions: []
"""
    p = _write_yaml(tmp_path, yaml_text, "bad_start.yaml")
    with pytest.raises(ValueError, match="start_state"):
        SingleTapeTM.from_yaml(p)


def test_yaml_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="bulunamadı"):
        SingleTapeTM.from_yaml(tmp_path / "yok.yaml")


def test_run_rejects_input_outside_alphabet() -> None:
    tm = SingleTapeTM.from_yaml(FIXTURES_DIR / "binary_increment.yaml")
    with pytest.raises(ValueError, match="input_alphabet"):
        tm.run("1012", max_steps=100)


def test_tape_extends_to_negative_positions() -> None:
    t = Tape("ab", "B")
    t.write(-3, "X")
    assert t.read(-3) == "X"
    assert t.read(-1) == "B"
    assert t.read(0) == "a"
    assert t.read(1) == "b"
    assert t.to_string() == "XBBab"

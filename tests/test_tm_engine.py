"""SingleTapeTM motoru için birim testleri.

Test kapsamı (ödev rubriğine uygun):
* 3 farklı TM × 5 girdi parametrize (binary_increment, unary_increment,
  even_a) — toplam 15 davranışsal test örneği.
* Durma koşulları: accept (başlangıçta), no_transition, timeout.
* History semantiği: ``len(history) == steps + 1`` ve adım numaralarının
  sıralılığı.
* Verbose mod çıktı biçimi.
* Hatalı YAML / hatalı δ kuralları için anlamlı ``ValueError``.
* Tape sınıfının iki yönlü genişleme davranışı.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from turinglab import SingleTapeTM, Tape


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _write_yaml(tmp_path: Path, text: str, name: str = "tm.yaml") -> Path:
    """Verilen YAML metnini geçici bir dosyaya yazıp yolunu döner."""
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# 3 farklı TM × 5'er girdi  (run() doğruluğu)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# History semantiği
# ---------------------------------------------------------------------------


def test_history_length_matches_steps() -> None:
    tm = SingleTapeTM.from_yaml(FIXTURES_DIR / "binary_increment.yaml")
    r = tm.run("1011", max_steps=2000)
    assert len(r.history) == r.steps + 1
    # İlk konfigürasyon başlangıç durumudur.
    assert r.history[0].step == 0
    assert r.history[0].state == tm.start_state
    assert r.history[0].head_position == 0


def test_history_records_step_progression() -> None:
    tm = SingleTapeTM.from_yaml(FIXTURES_DIR / "unary_increment.yaml")
    r = tm.run("111", max_steps=100)
    for i, cfg in enumerate(r.history):
        assert cfg.step == i
    # Son konfigürasyon kabul durumunda olmalı.
    assert r.history[-1].state in tm.accept_states


# ---------------------------------------------------------------------------
# Durma koşulları
# ---------------------------------------------------------------------------


def test_timeout(tmp_path: Path) -> None:
    """Sonsuz döngüye giren bir TM ``max_steps`` ile durmalı."""
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
    """Eşleşen δ kuralı yoksa ``no_transition`` ile durulmalı."""
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
    # 1, 1 başarıyla okundu; sonra 0'da kuralsız kaldı.
    assert r.steps == 2


def test_accept_at_start(tmp_path: Path) -> None:
    """Başlangıç durumu accept ise kabul ile birlikte sıfır adımda durulmalı."""
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


# ---------------------------------------------------------------------------
# Verbose mod
# ---------------------------------------------------------------------------


def test_verbose_format(capsys) -> None:
    """``verbose=True`` her adımı şartnameye uygun biçimde basmalı."""
    tm = SingleTapeTM.from_yaml(FIXTURES_DIR / "unary_increment.yaml")
    tm.run("1", max_steps=20, verbose=True)
    out = capsys.readouterr().out
    lines = [ln for ln in out.splitlines() if ln.strip()]
    assert len(lines) >= 2, "Verbose mod en az iki satır basmalı"
    assert lines[0].startswith("Adım 0 |"), "İlk satır 'Adım 0' ile başlamalı"
    for ln in lines:
        assert "[" in ln and "]" in ln, "Kafa konumu köşeli parantezle gösterilmeli"
        assert "Durum:" in ln
        assert "Şerit:" in ln
    # Son satır halt göstergesini içermeli.
    assert "(durdu:" in lines[-1]


# ---------------------------------------------------------------------------
# Hatalı YAML / hatalı δ kuralları
# ---------------------------------------------------------------------------


def test_yaml_missing_field(tmp_path: Path) -> None:
    yaml_text = """
states: [q0]
input_alphabet: ["1"]
tape_alphabet: ["1", "B"]
blank: B
start_state: q0
# accept_states ve transitions kasıtlı olarak yok
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
    """Girdide ``input_alphabet`` dışı sembol varsa ``ValueError`` fırlatılır."""
    tm = SingleTapeTM.from_yaml(FIXTURES_DIR / "binary_increment.yaml")
    with pytest.raises(ValueError, match="input_alphabet"):
        tm.run("1012", max_steps=100)


# ---------------------------------------------------------------------------
# Tape sınıfı (sparse + iki yönlü genişleme)
# ---------------------------------------------------------------------------


def test_tape_extends_to_negative_positions() -> None:
    t = Tape("ab", "B")
    t.write(-3, "X")
    assert t.read(-3) == "X"
    assert t.read(-1) == "B"
    assert t.read(0) == "a"
    assert t.read(1) == "b"
    # Yazılmış aralık [-3..1]; arada okunmamış hücreler blank ile dolar.
    assert t.to_string() == "XBBab"

"""Bölüm 2'de tasarlanan TM'ler için davranış testleri."""
from __future__ import annotations

from pathlib import Path

import pytest

from turinglab import SingleTapeTM


MACHINES_DIR = Path(__file__).parent.parent / "machines"


def _binary_result(final_tape: str) -> str:
    """Şeritteki X ve B kalıntılarını ayıkla, ikili sayıyı döner."""
    return final_tape.replace("X", "").strip("B")


@pytest.mark.parametrize(
    "input_string, expected",
    [
        ("", "0"),
        ("1", "1"),
        ("11", "10"),
        ("111", "11"),
        ("1111", "100"),
        ("11111", "101"),
    ],
)
def test_unary_to_binary(input_string: str, expected: str) -> None:
    tm = SingleTapeTM.from_yaml(MACHINES_DIR / "unary_to_binary.yaml")
    r = tm.run(input_string, max_steps=10000)
    assert r.accepted is True
    assert r.reason == "accept"
    assert _binary_result(r.final_tape) == expected


def test_unary_to_binary_large_input() -> None:
    """Daha büyük bir girdiyle de doğru sonuç vermeli (7 -> 111)."""
    tm = SingleTapeTM.from_yaml(MACHINES_DIR / "unary_to_binary.yaml")
    r = tm.run("1" * 7, max_steps=10000)
    assert r.accepted is True
    assert _binary_result(r.final_tape) == "111"


def test_unary_to_binary_input_alphabet_only_one() -> None:
    """Girdi alfabesi yalnız '1' olduğundan farklı sembol verilirse ValueError."""
    tm = SingleTapeTM.from_yaml(MACHINES_DIR / "unary_to_binary.yaml")
    with pytest.raises(ValueError, match="input_alphabet"):
        tm.run("110", max_steps=100)


@pytest.mark.parametrize(
    "input_string, expected_accept",
    [
        # kabul (1. > 2.)
        ("1#0", True),
        ("10#1", True),
        ("1100#1011", True),
        # ret (1. <= 2.)
        ("0#1", False),
        ("1011#1100", False),
        ("1011#1011", False),
    ],
)
def test_binary_compare(input_string: str, expected_accept: bool) -> None:
    tm = SingleTapeTM.from_yaml(MACHINES_DIR / "binary_compare.yaml")
    r = tm.run(input_string, max_steps=10000)
    assert r.accepted is expected_accept


def test_binary_compare_first_longer_with_lt_position() -> None:
    """Erken bir pozisyonda 2. büyük olsa bile 1. daha uzunsa 1. kabul edilir."""
    tm = SingleTapeTM.from_yaml(MACHINES_DIR / "binary_compare.yaml")
    r = tm.run("11011#1110", max_steps=10000)  # 27 > 14
    assert r.accepted is True


def test_binary_compare_second_longer() -> None:
    tm = SingleTapeTM.from_yaml(MACHINES_DIR / "binary_compare.yaml")
    r = tm.run("11#100", max_steps=10000)  # 3 < 4
    assert r.accepted is False


def test_binary_compare_equal_zero() -> None:
    """Sıfır eşitliği: 0#0 ret (kesinlikle büyük değil)."""
    tm = SingleTapeTM.from_yaml(MACHINES_DIR / "binary_compare.yaml")
    r = tm.run("0#0", max_steps=100)
    assert r.accepted is False

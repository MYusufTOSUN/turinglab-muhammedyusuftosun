"""Tek-şeritli deterministic Turing makinesi motoru."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, Sequence

import yaml


class Move(str, Enum):
    """Kafa hareket yönü: sol (L) veya sağ (R)."""

    LEFT = "L"
    RIGHT = "R"

    @classmethod
    def from_str(cls, value: str) -> "Move":
        """'L' veya 'R' string'ini Move değerine çevirir."""
        normalized = (value or "").strip().upper()
        for member in cls:
            if member.value == normalized:
                return member
        raise ValueError(
            f"Geçersiz hareket yönü: {value!r}. Beklenen: 'L' veya 'R'."
        )


@dataclass(frozen=True)
class Transition:
    """Tek bir δ kuralı: (state, read) -> (next_state, write, move)."""

    state: str
    read: str
    next_state: str
    write: str
    move: Move


@dataclass
class Configuration:
    """Bir adımdaki TM görüntüsü (durum, şerit, kafa konumu)."""

    step: int
    state: str
    tape: str
    head_position: int


@dataclass
class RunResult:
    """run() çağrısının sonucunu paketleyen yapı."""

    accepted: bool
    reason: str
    steps: int
    final_tape: str
    history: list[Configuration] = field(default_factory=list)


class Tape:
    """Sparse dict tabanlı, iki yönlü genişleyebilen Turing şeridi."""

    def __init__(self, input_string: str, blank: str) -> None:
        if len(blank) != 1:
            raise ValueError(
                f"Blank sembol tek karakter olmalı, gelen: {blank!r}"
            )
        self.blank = blank
        self._cells: dict[int, str] = {}
        for i, sym in enumerate(input_string):
            self._cells[i] = sym

    def read(self, position: int) -> str:
        """Verilen konumdaki sembolü döner; yazılmamışsa blank."""
        return self._cells.get(position, self.blank)

    def write(self, position: int, symbol: str) -> None:
        """Verilen konuma tek karakterlik bir sembol yazar."""
        if len(symbol) != 1:
            raise ValueError(f"Yazılan sembol tek karakter olmalı: {symbol!r}")
        # Blank yazmak hücreyi 'silmek'tir; min/max sınırını şişirmesin.
        if symbol == self.blank:
            self._cells.pop(position, None)
        else:
            self._cells[position] = symbol

    @property
    def min_position(self) -> int:
        return min(self._cells) if self._cells else 0

    @property
    def max_position(self) -> int:
        return max(self._cells) if self._cells else 0

    def to_string(self, head_position: int | None = None) -> str:
        """Yazılmış aralığı string olarak döner; head verilirse aralığı genişletir."""
        if not self._cells and head_position is None:
            return ""
        if not self._cells:
            return self.blank
        lo, hi = self.min_position, self.max_position
        if head_position is not None:
            lo = min(lo, head_position)
            hi = max(hi, head_position)
        return "".join(self._cells.get(i, self.blank) for i in range(lo, hi + 1))

    def render(self, head_position: int) -> str:
        """Şeridi 'ab[c]de' biçiminde, kafayı köşeli parantezle göstererek döner."""
        if not self._cells:
            return f"[{self.blank}]"
        lo = min(self.min_position, head_position)
        # Spec örneğindeki gibi sağ uçta bir blank hücreyi de göster.
        hi = max(self.max_position + 1, head_position)
        parts: list[str] = []
        for i in range(lo, hi + 1):
            sym = self._cells.get(i, self.blank)
            parts.append(f"[{sym}]" if i == head_position else sym)
        return "".join(parts)


class SingleTapeTM:
    """Tek-şeritli deterministic Turing makinesi."""

    def __init__(
        self,
        *,
        name: str,
        states: Sequence[str],
        input_alphabet: Sequence[str],
        tape_alphabet: Sequence[str],
        blank: str,
        start_state: str,
        accept_states: Sequence[str],
        reject_states: Sequence[str],
        transitions: Iterable[Transition],
        description: str = "",
    ) -> None:
        self.name = name
        self.description = description
        self.states = tuple(states)
        self.input_alphabet = tuple(input_alphabet)
        self.tape_alphabet = tuple(tape_alphabet)
        self.blank = blank
        self.start_state = start_state
        self.accept_states = frozenset(accept_states)
        self.reject_states = frozenset(reject_states)

        self._transitions: dict[tuple[str, str], Transition] = {}
        for t in transitions:
            key = (t.state, t.read)
            if key in self._transitions:
                raise ValueError(
                    f"Çift δ kuralı: state={t.state!r}, read={t.read!r}. "
                    "Aynı (durum, sembol) çiftine yalnızca tek geçiş tanımlanabilir."
                )
            self._transitions[key] = t

        self._validate()

    def transition(self, state: str, symbol: str) -> Transition | None:
        """δ(state, symbol) kuralını döner; tanımsızsa None."""
        return self._transitions.get((state, symbol))

    def _validate(self) -> None:
        """Alfabe, durumlar ve geçişler için yapısal tutarlılık denetimi."""
        if len(self.blank) != 1:
            raise ValueError(
                f"Blank sembol tek karakter olmalı, gelen: {self.blank!r}"
            )

        tape_set = set(self.tape_alphabet)
        if self.blank not in tape_set:
            raise ValueError(
                f"Blank sembol {self.blank!r} tape_alphabet içinde değil."
            )

        input_set = set(self.input_alphabet)
        if not input_set <= tape_set:
            missing = input_set - tape_set
            raise ValueError(
                "input_alphabet, tape_alphabet'in alt kümesi olmalı. "
                f"Eksik: {sorted(missing)}"
            )
        if self.blank in input_set:
            raise ValueError(
                f"Blank sembol ({self.blank!r}) input_alphabet içinde olmamalı."
            )

        state_set = set(self.states)
        if self.start_state not in state_set:
            raise ValueError(
                f"start_state={self.start_state!r} states listesinde yok."
            )

        unknown_accept = self.accept_states - state_set
        if unknown_accept:
            raise ValueError(
                f"accept_states içinde tanımsız durumlar: {sorted(unknown_accept)}"
            )
        unknown_reject = self.reject_states - state_set
        if unknown_reject:
            raise ValueError(
                f"reject_states içinde tanımsız durumlar: {sorted(unknown_reject)}"
            )

        common = self.accept_states & self.reject_states
        if common:
            raise ValueError(
                f"Aynı durum hem accept hem reject olamaz: {sorted(common)}"
            )

        for (state, read), t in self._transitions.items():
            if state not in state_set:
                raise ValueError(f"Geçişin kaynak durumu tanımsız: {state!r}")
            if t.next_state not in state_set:
                raise ValueError(
                    f"Geçişin hedef durumu tanımsız: {t.next_state!r} "
                    f"(kural: {state!r}, {read!r})"
                )
            if read not in tape_set:
                raise ValueError(
                    f"Geçişte okunan sembol tape_alphabet'te yok: {read!r} "
                    f"(kural: {state!r}, {read!r})"
                )
            if t.write not in tape_set:
                raise ValueError(
                    f"Geçişte yazılan sembol tape_alphabet'te yok: {t.write!r} "
                    f"(kural: {state!r}, {read!r})"
                )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "SingleTapeTM":
        """YAML dosyasından TM yükler. Hatalı format/eksik alan için ValueError fırlatır.

        Args:
            path: YAML dosyasının yolu.

        Returns:
            Doğrulanmış SingleTapeTM örneği.
        """
        p = Path(path)
        if not p.exists():
            raise ValueError(f"YAML dosyası bulunamadı: {p}")
        try:
            with p.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise ValueError(f"YAML çözümleme hatası ({p}): {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(
                f"YAML kök öğesi sözlük olmalı; bulunan: {type(data).__name__}"
            )

        required = {
            "states", "input_alphabet", "tape_alphabet", "blank",
            "start_state", "accept_states", "transitions",
        }
        missing = required - data.keys()
        if missing:
            raise ValueError(f"YAML'da eksik alanlar: {sorted(missing)}")

        raw = data["transitions"]
        if not isinstance(raw, list):
            raise ValueError("transitions bir liste olmalı.")

        transitions: list[Transition] = []
        required_t = {"state", "read", "next", "write", "move"}
        for idx, item in enumerate(raw):
            if not isinstance(item, dict):
                raise ValueError(f"transitions[{idx}] bir sözlük olmalı.")
            missing_t = required_t - item.keys()
            if missing_t:
                raise ValueError(
                    f"transitions[{idx}] içinde eksik alanlar: {sorted(missing_t)}"
                )
            try:
                move = Move.from_str(str(item["move"]))
            except ValueError as exc:
                raise ValueError(f"transitions[{idx}]: {exc}") from exc
            transitions.append(
                Transition(
                    state=str(item["state"]),
                    read=str(item["read"]),
                    next_state=str(item["next"]),
                    write=str(item["write"]),
                    move=move,
                )
            )

        return cls(
            name=str(data.get("name", p.stem)),
            description=str(data.get("description", "")),
            states=[str(s) for s in data["states"]],
            input_alphabet=[str(s) for s in data["input_alphabet"]],
            tape_alphabet=[str(s) for s in data["tape_alphabet"]],
            blank=str(data["blank"]),
            start_state=str(data["start_state"]),
            accept_states=[str(s) for s in data["accept_states"]],
            reject_states=[str(s) for s in data.get("reject_states", [])],
            transitions=transitions,
        )

    def run(
        self,
        input_string: str,
        *,
        max_steps: int = 1000,
        verbose: bool = False,
    ) -> RunResult:
        """Makineyi girdi üzerinde çalıştırır.

        Üç şekilde durur: kabul durumuna ulaşma (accept), eşleşen δ kuralı
        bulunamaması (no_transition), max_steps aşımı (timeout).
        verbose=True ise her adım stdout'a basılır.

        Args:
            input_string: Şerite yerleştirilecek başlangıç girdisi.
            max_steps: Maksimum adım bütçesi.
            verbose: Adımlar stdout'a basılsın mı?

        Returns:
            Çalışmanın sonucunu içeren RunResult.
        """
        if max_steps < 0:
            raise ValueError(f"max_steps negatif olamaz: {max_steps}")

        allowed = set(self.input_alphabet)
        for ch in input_string:
            if ch not in allowed:
                raise ValueError(
                    f"Girdi sembolü {ch!r} input_alphabet içinde değil."
                )

        tape = Tape(input_string, self.blank)
        state = self.start_state
        head = 0

        history: list[Configuration] = [
            Configuration(
                step=0,
                state=state,
                tape=tape.to_string(head),
                head_position=head,
            )
        ]

        def emit(step_num: int, suffix: str) -> None:
            if verbose:
                print(
                    f"Adım {step_num} | Durum: {state} | "
                    f"Şerit: {tape.render(head)} | {suffix}"
                )

        if state in self.accept_states:
            emit(0, "(durdu: accept)")
            return RunResult(
                accepted=True,
                reason="accept",
                steps=0,
                final_tape=tape.to_string(head),
                history=history,
            )

        for step_num in range(1, max_steps + 1):
            symbol = tape.read(head)
            t = self.transition(state, symbol)
            if t is None:
                emit(step_num - 1, "(durdu: no_transition)")
                return RunResult(
                    accepted=False,
                    reason="no_transition",
                    steps=step_num - 1,
                    final_tape=tape.to_string(head),
                    history=history,
                )

            emit(step_num - 1, f"Hareket: {t.move.value}")

            tape.write(head, t.write)
            head += 1 if t.move == Move.RIGHT else -1
            state = t.next_state
            history.append(
                Configuration(
                    step=step_num,
                    state=state,
                    tape=tape.to_string(head),
                    head_position=head,
                )
            )

            if state in self.accept_states:
                emit(step_num, "(durdu: accept)")
                return RunResult(
                    accepted=True,
                    reason="accept",
                    steps=step_num,
                    final_tape=tape.to_string(head),
                    history=history,
                )

        emit(max_steps, "(durdu: timeout)")
        return RunResult(
            accepted=False,
            reason="timeout",
            steps=max_steps,
            final_tape=tape.to_string(head),
            history=history,
        )

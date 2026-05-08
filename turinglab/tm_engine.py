"""Tek-şeritli deterministic Turing makinesi motoru.

Bu modül, YAML üzerinden tanımlanan Turing makinelerini yükleyen,
biçimsel tutarlılığını doğrulayan ve çalıştıran çekirdek sınıfları
içerir. Şerit temsili olarak ``dict[int, str]`` (sparse) tercih
edilmiştir; bu sayede şerit hem sağa hem sola istenildiği kadar
genişleyebilir ve negatif konumlar doğal olarak desteklenir.

Sınıflar:
    Move          : L/R hareket yönleri için enum.
    Transition    : Tek bir δ kuralını tutan veri sınıfı.
    Configuration : Çalışma sırasında tek bir adımdaki anlık görüntü.
    RunResult     : ``run()`` çağrısının sonucunu paketleyen yapı.
    Tape          : Sparse dict üzerine kurulu Turing şeridi.
    SingleTapeTM  : Yükleme + doğrulama + çalıştırma çekirdeği.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, Sequence

import yaml


class Move(str, Enum):
    """Kafa hareket yönleri.

    Spesifikasyon yalnızca sola (``L``) ve sağa (``R``) hareketi
    zorunlu kılar; bu yüzden motor da yalnızca bu iki yönü kabul eder.
    """

    LEFT = "L"
    RIGHT = "R"

    @classmethod
    def from_str(cls, value: str) -> "Move":
        """YAML'dan gelen string'i ``Move`` örneğine çevirir.

        Args:
            value: ``"L"`` veya ``"R"`` (büyük/küçük fark etmez).

        Returns:
            Karşılık gelen ``Move`` üyesi.

        Raises:
            ValueError: Beklenmeyen yön değeri için.
        """
        normalized = (value or "").strip().upper()
        for member in cls:
            if member.value == normalized:
                return member
        raise ValueError(
            f"Geçersiz hareket yönü: {value!r}. Beklenen: 'L' veya 'R'."
        )


@dataclass(frozen=True)
class Transition:
    """Tek bir δ(state, read) → (next_state, write, move) kuralı."""

    state: str
    read: str
    next_state: str
    write: str
    move: Move


@dataclass
class Configuration:
    """Çalışmanın belirli bir adımındaki TM anlık görüntüsü.

    Attributes:
        step: 0'dan başlayan adım indeksi (history içinde sıra).
        state: O an aktif olan kontrol durumunun adı.
        tape: Yazılmış aralıktaki (head dahil) şeridin string hali.
        head_position: Şerit üzerindeki mutlak kafa konumu (negatif olabilir).
    """

    step: int
    state: str
    tape: str
    head_position: int


@dataclass
class RunResult:
    """``SingleTapeTM.run()`` çağrısının sonuç paketi.

    Attributes:
        accepted: Makine kabul durumunda mı durdu?
        reason: Durma nedeni — ``"accept"``, ``"no_transition"`` ya da
            ``"timeout"``.
        steps: Toplam atılan adım sayısı.
        final_tape: Çalışma sonunda şeridin (yazılmış aralıkta) string hali.
        history: Adım 0'dan itibaren tüm konfigürasyonlar.
            ``len(history) == steps + 1`` (başlangıç da dahil).
    """

    accepted: bool
    reason: str
    steps: int
    final_tape: str
    history: list[Configuration] = field(default_factory=list)


class Tape:
    """Sparse (dict tabanlı) iki yönlü genişleyebilen Turing şeridi.

    Hücreler ``dict[int, str]`` içinde tutulur; eğer bir konum sözlükte
    yoksa, okuma sırasında ``blank`` döner. Bu yapının üç avantajı vardır:

    * Negatif konumlar (kafa sola taşarsa) doğal olarak desteklenir.
    * Bellek yalnızca yazılmış hücreler için tüketilir.
    * Şerit görselleştirilirken yazılmış aralık (min..max) baz alınır.
    """

    def __init__(self, input_string: str, blank: str) -> None:
        """Yeni bir şerit kurar.

        Args:
            input_string: Başlangıçta 0'dan itibaren şeride yazılacak girdi.
            blank: Boş hücreler için kullanılacak tek karakterlik sembol.

        Raises:
            ValueError: ``blank`` tek karakter değilse.
        """
        if len(blank) != 1:
            raise ValueError(
                f"Blank sembol tek karakter olmalı, gelen: {blank!r}"
            )
        self.blank: str = blank
        self._cells: dict[int, str] = {}
        for i, sym in enumerate(input_string):
            self._cells[i] = sym

    def read(self, position: int) -> str:
        """Verilen konumdaki sembolü döner; yazılmamışsa ``blank``."""
        return self._cells.get(position, self.blank)

    def write(self, position: int, symbol: str) -> None:
        """Verilen konuma sembolü yazar.

        Raises:
            ValueError: Yazılan sembol tek karakter değilse.
        """
        if len(symbol) != 1:
            raise ValueError(
                f"Yazılan sembol tek karakter olmalı: {symbol!r}"
            )
        self._cells[position] = symbol

    @property
    def min_position(self) -> int:
        """Yazılmış hücreler içindeki en küçük konum (yazma yoksa 0)."""
        return min(self._cells) if self._cells else 0

    @property
    def max_position(self) -> int:
        """Yazılmış hücreler içindeki en büyük konum (yazma yoksa 0)."""
        return max(self._cells) if self._cells else 0

    def to_string(self, head_position: int | None = None) -> str:
        """Yazılmış aralığın düz string halini döner.

        Args:
            head_position: Verilirse, gerekirse aralık kafa konumunu da
                kapsayacak şekilde genişletilir. ``None`` ise yalnızca
                yazılmış aralık döner.
        """
        if not self._cells and head_position is None:
            return ""
        if not self._cells:
            return self.blank
        lo = self.min_position
        hi = self.max_position
        if head_position is not None:
            lo = min(lo, head_position)
            hi = max(hi, head_position)
        return "".join(self._cells.get(i, self.blank) for i in range(lo, hi + 1))

    def render(self, head_position: int) -> str:
        """Şeridi, kafa konumu köşeli parantez içinde olacak şekilde döner.

        Verbose mod çıktısında kullanılan biçim:
        ``"ab[c]de"`` — kafa, c sembolü üzerindedir.
        """
        if not self._cells:
            return f"[{self.blank}]"
        lo = min(self.min_position, head_position)
        hi = max(self.max_position, head_position)
        parts: list[str] = []
        for i in range(lo, hi + 1):
            sym = self._cells.get(i, self.blank)
            parts.append(f"[{sym}]" if i == head_position else sym)
        return "".join(parts)


class SingleTapeTM:
    """Tek-şeritli deterministic Turing makinesi.

    Doğrudan parametrelerle veya ``SingleTapeTM.from_yaml(path)`` ile
    oluşturulabilir. ``__init__`` çağrıldığında otomatik olarak biçimsel
    tutarlılık doğrulaması (``_validate``) yapılır.
    """

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
        self.name: str = name
        self.description: str = description
        self.states: tuple[str, ...] = tuple(states)
        self.input_alphabet: tuple[str, ...] = tuple(input_alphabet)
        self.tape_alphabet: tuple[str, ...] = tuple(tape_alphabet)
        self.blank: str = blank
        self.start_state: str = start_state
        self.accept_states: frozenset[str] = frozenset(accept_states)
        self.reject_states: frozenset[str] = frozenset(reject_states)

        self._transitions: dict[tuple[str, str], Transition] = {}
        for t in transitions:
            key = (t.state, t.read)
            if key in self._transitions:
                raise ValueError(
                    f"Çift δ kuralı: state={t.state!r}, read={t.read!r}. "
                    "Deterministic TM'de aynı (durum, sembol) çiftine "
                    "yalnızca tek geçiş tanımlanabilir."
                )
            self._transitions[key] = t

        self._validate()

    def transition(self, state: str, symbol: str) -> Transition | None:
        """δ(state, symbol) — tanımlı değilse ``None``."""
        return self._transitions.get((state, symbol))

    def _validate(self) -> None:
        """Yapısal tutarlılık denetimi.

        Aşağıdaki koşullar sağlanmalıdır; sağlanmıyorsa ``ValueError``
        anlamlı bir mesajla fırlatılır:

        * blank tek karakter ve tape_alphabet içinde olmalı.
        * input_alphabet ⊆ tape_alphabet ve blank ∉ input_alphabet.
        * start_state ve accept/reject durumları states içinde tanımlı.
        * accept ile reject kümeleri ayrık olmalı.
        * Tüm geçişlerin durumları states içinde, sembolleri tape_alphabet
          içinde tanımlı olmalı.
        """
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
                raise ValueError(
                    f"Geçişin kaynak durumu tanımsız: {state!r}"
                )
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
        """Bir YAML dosyasından TM yükler.

        Eksik alan, hatalı yapı veya tutarsız tanımlar için anlamlı
        bir ``ValueError`` fırlatır.

        Args:
            path: YAML dosyasının yolu.

        Returns:
            Doğrulanmış, hazır ``SingleTapeTM`` örneği.
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
            "states",
            "input_alphabet",
            "tape_alphabet",
            "blank",
            "start_state",
            "accept_states",
            "transitions",
        }
        missing = required - data.keys()
        if missing:
            raise ValueError(f"YAML'da eksik alanlar: {sorted(missing)}")

        raw_transitions = data["transitions"]
        if not isinstance(raw_transitions, list):
            raise ValueError("transitions bir liste olmalı.")

        transitions: list[Transition] = []
        required_t = {"state", "read", "next", "write", "move"}
        for idx, item in enumerate(raw_transitions):
            if not isinstance(item, dict):
                raise ValueError(f"transitions[{idx}] bir sözlük olmalı.")
            missing_t = required_t - item.keys()
            if missing_t:
                raise ValueError(
                    f"transitions[{idx}] içinde eksik alanlar: "
                    f"{sorted(missing_t)}"
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
        """Makineyi belirtilen girdi üzerinde çalıştırır.

        Akış:
            1. Girdiyi şeride 0'dan itibaren yerleştir.
            2. Aktif durum başlangıç durumuna, kafa 0'a alınır.
            3. Her adımda δ(state, read) aranır; bulunamazsa
               ``no_transition`` ile durulur.
            4. Yeni duruma geçildiğinde aktif durum ``accept_states``
               içindeyse ``accept`` ile durulur.
            5. ``max_steps`` aşılırsa ``timeout`` ile durulur.

        Args:
            input_string: Şerite yerleştirilecek başlangıç girdisi.
                ``input_alphabet`` dışında bir sembol içeriyorsa
                ``ValueError`` fırlatılır.
            max_steps: Sonsuz döngüye karşı maksimum adım bütçesi (≥ 0).
            verbose: ``True`` ise her adım şu biçimde stdout'a basılır:
                ``Adım N | Durum: q | Şerit: ab[c]de | Hareket: R``.
                Durduğunda son satır ``... | (durdu: <reason>)`` ile biter.

        Returns:
            ``accept`` / ``no_transition`` / ``timeout`` durumlarından
            birinde sonlanan çalışmaya ait :class:`RunResult`.
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
            """Verbose modda tek bir satır basar."""
            if verbose:
                print(
                    f"Adım {step_num} | Durum: {state} | "
                    f"Şerit: {tape.render(head)} | {suffix}"
                )

        # Başlangıç durumu zaten accept ise hemen kabul et.
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

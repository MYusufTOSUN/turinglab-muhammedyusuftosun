"""TuringLab — Tek-şeritli Turing makinesi simülatörü.

Hesaplama Kuramı (Selçuk Üniversitesi · Bilgisayar Mühendisliği) dersi
final ödevi için geliştirilmiş; YAML üzerinden tanımlanan deterministic
Turing makinelerini yükleyip çalıştıran bir kütüphanedir.

Tipik kullanım:
    >>> from turinglab import SingleTapeTM
    >>> tm = SingleTapeTM.from_yaml("machines/binary_increment.yaml")
    >>> result = tm.run("1011", max_steps=1000)
    >>> result.accepted
    True
"""

from turinglab.tm_engine import (
    Configuration,
    Move,
    RunResult,
    SingleTapeTM,
    Tape,
    Transition,
)

__all__ = [
    "Configuration",
    "Move",
    "RunResult",
    "SingleTapeTM",
    "Tape",
    "Transition",
]

__version__ = "0.1.0"

from dataclasses import dataclass
from lark import Lark, Transformer, Tree, Token
from typing import Any

@dataclass(frozen=True)
class Numr:
    value: float

@dataclass(frozen=True)
class OpBin:
    op: str
    left: object
    right: object

@dataclass(frozen=True)
class Boolean:
    value: bool

@dataclass(frozen=True)
class String:
    value: str

@dataclass(frozen=True)
class Carattr:
    value: str
    def __post_init__(self):
        if len(self.value) != 1:
            raise ValueError("value deve contenere un solo carattere")

@dataclass(frozen=True)
class GenericVar:
    value: Any

@dataclass(frozen=True)
class Assegnazione:
    op: str
    leftpos=object
    rightpos=object

@dataclass(frozen=True)
class Condizione:
    op: OpBin
    allora: object
    altrimenti: object

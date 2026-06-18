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
class metimca:
    op: OpBin
    allora: object
    altrimenti: object

class Mestier:
        nome: str
        parametri: list[object]
        ritorno: object


@dataclass(frozen=True)
class Roba:
      nome: str
      variabili: list[object]
      funzioni: list[Mestier]

class Aspe:
      Condizione: Boolean
      Corpo: list[object]

class Ambress_ambress:
      Condizione: Boolean
      dichiarazione: Assegnazione
      VarOp: str
      Corpo: list[object]

class Assegnazi:
      tipo: str
      id: str

class return1:
      valor: object
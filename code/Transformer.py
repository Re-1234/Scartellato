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

@dataclass(frozen=True)
class Parametro:
        tipo: str
        nome: str
@dataclass(frozen=True)
class Mestier:
        nome: str
        parametri: list[Parametro]
        ritorno: object


@dataclass(frozen=True)
class Robba:
      nome: str
      variabili: list[object]
      funzioni: list[Mestier]

@dataclass(frozen=True)
class Aspe:
      Condizione: Boolean
      Corpo: list[object]

@dataclass(frozen=True)
class Ambress_Ambress:
      Condizione: Boolean
      dichiarazione: Assegnazione
      VarOp: str
      Corpo: list[object]

@dataclass(frozen=True)
class Assegnazione:
      tipo: str
      id: str

@dataclass(frozen=True)
class ReturnStatement:
      valor: object
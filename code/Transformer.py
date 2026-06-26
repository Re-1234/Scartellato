from dataclasses import dataclass

from typing import Any, List, Optional


@dataclass
class Start:
    program: List[Any]

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
class Stringa:
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
class Variabile:
    nome : str
    is_array: bool= False



@dataclass(frozen=True)
class Dichiarazione :
    tipo: object
    nome : Variabile
    valore: object

@dataclass(frozen=True)
class Block:
    statements: List[Any]

@dataclass(frozen=True)
class Assegnamento:
       name: str
       value: Any


@dataclass(frozen=True)
class CallStmt:
    nome_func: object
    args: List[Any]

@dataclass(frozen=True)
class Mettimmca:
    condizione : Any
    allora: Block
    altrimenti:  Optional[Block] = None

@dataclass(frozen=True)
class Aspe:
    Condizione: object
    Corpo: Block

@dataclass(frozen=True)
class Ambress_Ambress:
    dichiarazione: Dichiarazione | Variabile
    condizione: OpBin
    VarOperation: object
    Corpo: Block


@dataclass(frozen=True)
class Parametro:
        tipo: str
        nome: Variabile

@dataclass(frozen=True)
class Mestier:
        nome: str
        parametri: list[Parametro]
        ritorno: object
        corpo : list[object]
        is_array: bool = False


@dataclass(frozen=True)
class Costruttore:
    params: list
    corpo: Block

@dataclass(frozen=True)
class Robba:
      nome: str
      costruttore: Costruttore
      variabili: list[object]
      funzioni: list[Mestier]

@dataclass(frozen=True)
class ReturnStatement:
      valor: object
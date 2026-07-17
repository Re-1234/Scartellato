from dataclasses import dataclass
from operator import index

from typing import Any, List, Optional


@dataclass
class Start:
    program: List[Any]

@dataclass
class TipoDato:
    nome: str
    linea: int
    colonna: int


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
    value: object

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
class Variabile:
    nome : str
    index: int
    is_array: bool = False
    def __post_init__(self):
        if not isinstance(self.index, int):
            raise TypeError(f"index deve essere int, ricevuto {type(self.index)}")

@dataclass(frozen=True)
class Dichiarazione:
    tipo: TipoDato
    nome : Variabile
    valore: object

@dataclass(frozen=True)
class Block:
    statements: List[Any]


@dataclass(frozen=True)
class CallStmt:
    nome_func: str
    args: List[Any]

@dataclass(frozen=True)
class Mettimmca:
    condizione : OpBin
    allora: Block
    altrimenti:  Optional[Block] = None

@dataclass(frozen=True)
class Aspe:
    Condizione: OpBin
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
        nome: Variabile
        parametri: list[Parametro]
        ritorno: object
        corpo : Block
        is_array: bool = False


@dataclass(frozen=True)
class Costruttore:
    parametri: list[Parametro]
    corpo: Block

@dataclass(frozen=True)
class Robba:
      nome: str
      costruttore: Costruttore
      variabili: list[object]
      funzioni: list[Mestier]

@dataclass(frozen=True)
class ReturnStatement:
      valore: object

@dataclass(frozen=True)
class Break:
    pass

@dataclass(frozen=True)
class Arape_a_vocca:
    valore: str
    variabili: list[Variabile]

@dataclass(frozen=True)
class ChiamataOggetto:
    nome: Variabile
    variabile: Variabile
    Parametri: list[Parametro]

@dataclass(frozen=True)
class ChiamataCostruttore:
    nome:Variabile
    parametri : list[Parametro]

@dataclass(frozen=True)
class AccessoCampo:
    variabile: Variabile   # "c"
    campo: Variabile        # "var"
from dataclasses import dataclass
from lark import Lark, Transformer, Tree, Token

@dataclass(frozen=True)
class Numbr:
    value: float

@dataclass(frozen=True)
class OpBin:
    op: str
    left: object
    right: object


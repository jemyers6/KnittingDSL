from __future__ import annotations
from dataclasses import dataclass
from typing import List, Literal

# Expr
@dataclass(frozen=True)
class Expr:
    """Base class for all expressions."""
    pass


@dataclass(frozen=True)
class Num(Expr):
    value: str


@dataclass(frozen=True)
class Var(Expr):
    name: str


@dataclass(frozen=True)
class BinOp(Expr):
    op: Literal["+", "-", "*"]
    left: Expr
    right: Expr

# Motif
@dataclass(frozen=True)
class Motif:
    """Base class for all motifs."""
    pass


@dataclass(frozen=True)
class StitchMotif(Motif):
    op: str  # e.g. "K", "P", "K2TOG", "M1L"


@dataclass(frozen=True)
class RefMotif(Motif):
    name: str  # references a stitch definition

@dataclass(frozen=True)
class ParenMotif(Motif): # this is the same thing as a motif ref but inline instead of defined separately
    elements: List[Element] 

# Element
@dataclass(frozen=True)
class Element:
    motif: Motif
    repeat: Expr   # how many times to repeat the motif

# Statment
@dataclass(frozen=True)
class Statement:
    pass

class RowStatement(Statement):
    elements: List[Element]
    fill: bool = False

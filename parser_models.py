from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

# Expr
@dataclass(frozen=True)
class Expr:
    """Base class for all expressions."""
    pass


@dataclass(frozen=True)
class Num(Expr):
    value: int


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

# Element
@dataclass(frozen=True)
class Element:
    motif: Motif
    repeat: Expr   # how many times to repeat the motif
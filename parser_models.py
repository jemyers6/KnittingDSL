from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

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

@dataclass(frozen=True)
class RowStatement(Statement):
    elements: List[Element]
    fill: bool = False

@dataclass(frozen=True)
class CastOnStmt(Statement):
    count: Expr

@dataclass(frozen=True)
class BindOffStmt(Statement):
    count: Expr

@dataclass(frozen=True)
class RepeatStmt(Statement):
    times: Expr
    body: List[Statement]

@dataclass(frozen=True)
class WorkStmt(Statement):
    pattern_name: str
    args: List[Expr]

@dataclass(frozen=True)
class PrintStmt(Statement):
    message: str


# Pattern and Stitch Definitions
@dataclass(frozen=True)
class Pattern:
    name: str
    params: Optional[List[str]]         
    statements: List[Statement]   

@dataclass(frozen=True)
class StitchDef:
    name: str
    elements: List[Element]


# Program data classes
@dataclass(frozen=True)
class PatternCall:
    name: str
    args: Optional[List[str]]          

@dataclass(frozen=True)
class Program:
    stitch_defs: List[StitchDef]
    patterns: List[Pattern]
    entry: PatternCall               
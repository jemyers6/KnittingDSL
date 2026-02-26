from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
from parser_models import *
from typing import Tuple

class RuntimeErrorEval(Exception):
    pass


@dataclass
class Env:
    vars: Dict[str, int]
    width: int
    row: int = 0

class Interpreter:
    def __init__(self, program: "Program"):
        self.program = program

    def run_program(self) -> List[str]:
        call = self.program.entry
        pattern = next(
            (p for p in self.program.patterns if p.name == call.name),
            None
        )
        if pattern is None:
            raise RuntimeErrorEval(f"Unknown pattern '{call.name}'")

        env = self._bind_call_env(call, pattern)

        rows = self._run_pattern(pattern, env)

        formatted: List[str] = []
        for i, row in enumerate(rows):
            formatted.append(f"ROW {i}: " + " ".join(row))

        return formatted

    def _bind_call_env(self, call: "PatternCall", pattern: "Pattern") -> Env:
        if len(call.args) != len(pattern.params):
            raise RuntimeErrorEval(
                f"Pattern '{pattern.name}' expects {len(pattern.params)} args "
                f"but got {len(call.args)}"
            )

        vars_: Dict[str, int] = {}

        tmp_env = Env(vars=vars_, width=0)

        for param, arg_expr in zip(pattern.params, call.args):
            vars_[param] = self.eval_expr(arg_expr, tmp_env)

        if "width" in vars_: 
            width = vars_["width"]
        elif self.program.global_width is not None:
            width = self.program.global_width
        else:
            raise RuntimeErrorEval("No width provided (missing width param and no global_width)")

        if width < 0:
            raise RuntimeErrorEval(f"Width cannot be negative (got {width})")

        return Env(vars=vars_, width=width)

    def _run_pattern(self, pattern: "Pattern", env: Env) -> List[List[str]]:
        rows: List[List[str]] = []

        for stmt in pattern.statements:
            result = self.eval_statement(stmt, env)
            if result:
                for r in result:
                    rows.append(r)

        return rows
    
    def eval_statement(self, stmt: "Statement", env: Env) -> List[List[str]]:
        if isinstance(stmt, RowStatement):
            stitches = self.eval_row_statement(stmt, env)
            row_index = env.row
            env.row += 1
            return [stitches]

        if isinstance(stmt, RepeatStmt):
            return self.eval_repeat_statement(stmt, env)

        if isinstance(stmt, CastOnStmt):
            count = self.eval_expr(stmt.count, env)
            if count < 0:
                raise RuntimeErrorEval(...)
            env.width = count
            env.row += 1
            return [["CO"] * count]

        if isinstance(stmt, BindOffStmt):
            count = self.eval_expr(stmt.count, env)
            if count != env.width:
                raise RuntimeErrorEval(...)
            env.width = 0
            env.row += 1
            return [["BO"] * count]

        if isinstance(stmt, PrintStmt):
            print(stmt.message)
            return []

        if isinstance(stmt, WorkStmt):
            pattern_name = stmt.pattern_name
            pattern = next(
                (p for p in self.program.patterns if p.name == pattern_name),
                None
            )
            if pattern is None:
                raise RuntimeErrorEval(f"Unknown pattern '{pattern_name}'")

            call = PatternCall(name=pattern_name, args=stmt.args)

            call_env = self._bind_call_env_inherit(call, pattern, env)

            rows = self._run_pattern(pattern, call_env)

            env.row = call_env.row
            env.width = call_env.width  

            return rows  # if you're using row-separated output

        raise RuntimeErrorEval(f"Unimplemented statement type: {type(stmt).__name__}")
    
    def _bind_call_env_inherit(self, call: "PatternCall", pattern: "Pattern", caller_env: Env) -> Env:
        if len(call.args) != len(pattern.params):
            raise RuntimeErrorEval(
                f"Pattern '{pattern.name}' expects {len(pattern.params)} args "
                f"but got {len(call.args)}"
            )

        vars_: Dict[str, int] = dict(caller_env.vars)

        tmp_env = Env(vars=vars_, width=caller_env.width, row=caller_env.row)

        for param, arg_expr in zip(pattern.params, call.args):
            vars_[param] = self.eval_expr(arg_expr, tmp_env)

        if "width" in pattern.params:
            width = vars_["width"]
        else:
            width = caller_env.width

        if width < 0:
            raise RuntimeErrorEval(f"Width cannot be negative (got {width})")

        return Env(vars=vars_, width=width, row=caller_env.row) 
    
    def eval_repeat_statement(self, rep: "RepeatStmt", env: Env) -> List[List[str]]:
        n = self.eval_expr(rep.times, env)
        if n < 0:
            raise RuntimeErrorEval(f"Repeat times cannot be negative (got {n})")

        rows: List[List[str]] = []

        for _ in range(n):
            for stmt in rep.body:
                rows.extend(self.eval_statement(stmt, env))

        return rows

    def debug_eval_expr(self, expr: "Expr", env_vars: Dict[str, int]) -> int:
        env = Env(vars=dict(env_vars), width=env_vars.get("width", 0))
        return self.eval_expr(expr, env)

    def debug_expand_element(self, element: "Element", env_vars: Dict[str, int]) -> List[str]:
        width = env_vars.get("width", self.program.global_width or 0)
        env = Env(vars=dict(env_vars), width=width)
        return self.expand_element(element, env)

    def eval_expr(self, expr: "Expr", env: Env) -> int:
        if isinstance(expr, Num):
            return expr.value
        if isinstance(expr, Var):
            if expr.name not in env.vars: 
                raise RuntimeErrorEval(f"Undefined variable '{expr.name}'")
            if expr.name == "width": 
                return env.width    
            return env.vars[expr.name]
        if isinstance(expr, BinOp):
            a = self.eval_expr(expr.left, env)
            b = self.eval_expr(expr.right, env)
            if expr.op == "+":
                return a + b
            if expr.op == "-":
                return a - b
            if expr.op == "*":
                return a * b
            raise RuntimeErrorEval(f"Unknown operator '{expr.op}'")
        raise RuntimeErrorEval(f"Unknown Expr node {type(expr).__name__}")

    def expand_element(self, element: "Element", env: Env, stack: Optional[List[str]] = None) -> List[str]:
        n = self.eval_expr(element.repeat, env)
        if n < 0:
            raise RuntimeErrorEval(f"Repeat count cannot be negative (got {n})")

        unit = self.expand_motif(element.motif, env, stack)

        if not unit: # if the element was an decrease 
            return []
        
        return unit * n
    
    def expand_element_stats(
        self,
        element: "Element",
        env: Env,
        stack: Optional[List[str]] = None
    ) -> Tuple[int, int, List[str]]:
        """
        Returns: (consumed, produced, output_stitches)
        - consumed: how many existing stitches this element uses up
        - produced: how many new stitches this element creates
        - output_stitches: list length == produced
        """
        n = self.eval_expr(element.repeat, env)
        if n < 0:
            raise RuntimeErrorEval(f"Repeat count cannot be negative (got {n})")

        c_unit, p_unit, out_unit = self.expand_motif_stats(element.motif, env, stack)

        return (c_unit * n, p_unit * n, out_unit * n)

    def expand_motif(
        self,
        motif: "Motif",
        env: "Env",
        stack: Optional[List[str]] = None
    ) -> List[str]:
        if stack is None:
            stack = []

        if isinstance(motif, StitchMotif):
            op = motif.op

            match op:
                case "K" | "P" :
                    return [op]

                case "M1L" | "M1R" | "KFB":
                    return ["K", "K"]   # counts as 2 stitches

                case "SSK" | "K2TOG":
                    return []         # counts as 0 stitches
                case _:
                    raise RuntimeErrorEval(f"Unknown stitch operator '{motif.op}'")
        if isinstance(motif, ParenMotif):
            out: List[str] = []
            for el in motif.elements:
                out.extend(self.expand_element(el, env, stack))
            return out

        if isinstance(motif, RefMotif):
            name = motif.name
            if name not in self.program.stitch_defs:
                raise RuntimeErrorEval(f"Undefined stitch '{name}'")

            if name in stack:
                raise RuntimeErrorEval("Cycle in stitch defs: " + " -> ".join(stack + [name]))

            stack.append(name)
            defn = self.program.stitch_defs[name]  
            out: List[str] = []
            for el in defn.elements:
                out.extend(self.expand_element(el, env, stack))
            stack.pop()
            return out

        raise RuntimeErrorEval(f"Unknown motif type: {type(motif).__name__}")
    
    def expand_motif_stats(
        self,
        motif: "Motif",
        env: Env,
        stack: Optional[List[str]] = None
    ) -> Tuple[int, int, List[str]]:
        """
        Returns: (consumed, produced, output_stitches)
        """
        if stack is None:
            stack = []

        if isinstance(motif, StitchMotif):
            op = motif.op

            match op:
                case "K" | "P":
                    return (1, 1, [op])

                case "M1L" | "M1R" | "KFB":
                    return (1, 2, ["K", "K"])

                case "SSK" | "K2TOG":
                    return (1, 0, [])

                case _:
                    raise RuntimeErrorEval(f"Unknown stitch operator '{motif.op}'")

        if isinstance(motif, ParenMotif):
            c_total = 0
            p_total = 0
            out: List[str] = []
            for el in motif.elements:
                c, p, o = self.expand_element_stats(el, env, stack)
                c_total += c
                p_total += p
                out.extend(o)
            return (c_total, p_total, out)

        if isinstance(motif, RefMotif):
            name = motif.name
            stitch_def = next((sd for sd in self.program.stitch_defs if sd.name == name), None)
            if stitch_def is None:
                raise RuntimeErrorEval(f"Unknown stitch definition '{name}'")

            if name in stack:
                raise RuntimeErrorEval("Cycle in stitch defs: " + " -> ".join(stack + [name]))

            stack.append(name)
            defn = stitch_def  

            c_total = 0
            p_total = 0
            out: List[str] = []
            for el in defn.elements:
                c, p, o = self.expand_element_stats(el, env, stack)
                c_total += c
                p_total += p
                out.extend(o)

            stack.pop()
            return (c_total, p_total, out)

        raise RuntimeErrorEval(f"Unknown motif type: {type(motif).__name__}")
        
    def eval_row_statement(self, row: "RowStatement", env: Env) -> List[str]:
        if not row.elements:
            raise RuntimeErrorEval("Row has no elements")

        # Expand row (without fill first)
        consumed = 0
        produced = 0
        out: List[str] = []

        for el in row.elements:
            c, p, o = self.expand_element_stats(el, env)
            consumed += c
            produced += p
            out.extend(o)

        if consumed > env.width:
             raise RuntimeErrorEval(
                f"Row consumes {consumed} stitches, exceeds current width {env.width}"
        )
        if not row.fill:
            # Must consume exactly current width
            if consumed != env.width:
                raise RuntimeErrorEval(
                    f"Row consumes {consumed} stitches but current width is {env.width}"
                )
            # Update width to produced stitch count for next row
            env.width = produced
            return out

        remaining_consume = env.width - consumed
        if remaining_consume == 0:
            env.width = produced
            return out

        last_el = row.elements[-1]
        c_unit, p_unit, out_unit = self.expand_element_stats(
            Element(motif=last_el.motif, repeat=Num(1)),  
            env
        )

        if c_unit == 0:
            raise RuntimeErrorEval("Cannot fill with an element that consumes 0 stitches")

        if remaining_consume % c_unit != 0:
            raise RuntimeErrorEval(
                f"Fill cannot complete row: remaining consume {remaining_consume} "
                f"is not a multiple of last element consume-unit {c_unit}"
            )

        times = remaining_consume // c_unit
        consumed += c_unit * times
        produced += p_unit * times
        out.extend(out_unit * times)

        if consumed != env.width:
            raise RuntimeErrorEval(
                f"Internal error: after fill consumed {consumed} != width {env.width}"
            )

        # Update width for next row
        env.width = produced
        return out
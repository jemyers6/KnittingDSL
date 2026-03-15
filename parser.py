from __future__ import annotations
from ast import pattern
from lexer import Lexer, Token, TokenType
import sys
from dataclasses import dataclass, field
from typing import List, Optional
from parser_models import *
from interpreter import Interpreter

class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.global_width = 0

    def syntax_error(self):
        print("SYNTAX ERROR")
        sys.exit(0)

    def consume(self, expected_type, context: str = ""):
        token = self.lexer.next_token()

        if isinstance(expected_type, (set, tuple, list)):
            allowed = tuple(expected_type)
        else:
            allowed = (expected_type,)

        if token.token_type not in allowed:
            expected_names = ", ".join(t.name for t in allowed)
            detail = f" while parsing {context}" if context else ""
            raise SyntaxError(
                f"Expected {{{expected_names}}} but found {token.token_type.name} "
                f"({token.lexeme!r}) on line {token.line_no}{detail}"
            )

        return token
    
    def parse_input(self) -> Program:
        program = self.parse_program()
        self.consume(TokenType.EOF)
        return program

    def parse_program(self) -> Program:
        # program  → stitch_def_list pattern_list execute_stmt
        stitchDefs: List[StitchDef] = []
        stitch_defs = self.parse_stitch_def_list(stitchDefs)
        patterns: List[Pattern] = []
        patterns = self.parse_pattern_list(patterns)
        entry = self.parse_execute_stmt()
        return Program(stitch_defs, patterns, entry)


    def parse_stitch_def_list(self, stitchDefs: List[StitchDef]) -> List[StitchDef]:
        # stitch_def_list → stitch_def stitch_def_list | epsilon
        t = self.lexer.peek(1)
        if t.token_type == TokenType.STITCH:
            stitchDefs.append(self.parse_stitch_def())
            return self.parse_stitch_def_list(stitchDefs)
        elif t.token_type in {TokenType.PATTERN, TokenType.EXECUTE}:
            return stitchDefs
        else:
            self.syntax_error()
    
    def parse_stitch_def(self) -> StitchDef:
        # stitch_def → STITCH ID EQUALS motif_line_list SEMICOLON 
        self.consume(TokenType.STITCH)
        name = self.consume(TokenType.ID).lexeme
        self.consume(TokenType.EQUALS)
        elements = self.parse_motif_line_list()
        self.consume(TokenType.SEMICOLON)
        return StitchDef(name, elements)
    
    def parse_pattern_list(self, patterns: List[Pattern]) -> List[Pattern]:
        # pattern_list → pattern pattern_list | epsilon
        t = self.lexer.peek(1)
        if t.token_type == TokenType.PATTERN:
            patterns.append(self.parse_pattern())
            return self.parse_pattern_list(patterns)
        elif t.token_type == TokenType.EXECUTE:
            return patterns
        else:
            self.syntax_error()

        # elements: List[Element] = []
        # elements.append(self.parse_element())
        # self.parse_motif_line(elements)

    def parse_pattern(self) -> Pattern:
        # pattern → PATTERN ID LPAREN param_header RPAREN LCBRAC pattern_body RCBRAC
        self.consume(TokenType.PATTERN)
        name = self.consume(TokenType.ID).lexeme
        self.consume(TokenType.LPAREN)
        params_exprs = self.parse_param_header()
        params = [p.name for p in params_exprs]
        self.consume(TokenType.RPAREN)
        self.consume(TokenType.LCBRAC)
        statements = self.parse_pattern_body()
        self.consume(TokenType.RCBRAC)
        return Pattern(name, params, statements)

    def parse_param_header(self) -> List[Expr]:
        # param_header → param_list | epsilon
        t = self.lexer.peek(1)
        if t.token_type == TokenType.ID:
            return self.parse_param_list()
        elif t.token_type == TokenType.RPAREN:
            return []
        else:
            self.syntax_error()

    def parse_param_list(self) -> List[Expr]:
        # param_list → ID COMMA param_list | ID
        name = Var(self.consume(TokenType.ID).lexeme)
        t = self.lexer.peek(1)
        if t.token_type == TokenType.COMMA:
            self.consume(TokenType.COMMA)
            return [name] + self.parse_param_list()
        elif t.token_type == TokenType.RPAREN:
            return [name]
        else:
            self.syntax_error()
    
    def parse_pattern_body(self) -> List[Statement]:
        # pattern_body → pattern_stmt pattern_body | pattern_stmt
        stmt = self.parse_pattern_stmt()
        t = self.lexer.peek(1)
        if t.token_type in {TokenType.KNIT, 
                            TokenType.PURL, 
                            TokenType.KFB, 
                            TokenType.M1L, 
                            TokenType.M1R, 
                            TokenType.SSK, 
                            TokenType.K2TOG,
                            TokenType.CAST_ON, 
                            TokenType.BIND_OFF, 
                            TokenType.REPEAT, 
                            TokenType.ID, 
                            TokenType.WORK, 
                            TokenType.PRINT}:
            return [stmt] + self.parse_pattern_body()
        elif t.token_type == TokenType.RCBRAC:
            return [stmt]
        else:
            self.syntax_error()

    def parse_pattern_stmt(self) -> Statement:
        # pattern_stmt → cast_on_stmt | bind_off_stmt | repeat_block | row_stmt | work_stmt | print_stmt
        t = self.lexer.peek(1)
        if t.token_type == TokenType.CAST_ON:
            return self.parse_cast_on_stmt()
        elif t.token_type == TokenType.BIND_OFF:
            return self.parse_bind_off_stmt()
        elif t.token_type == TokenType.REPEAT:
            return self.parse_repeat_block()
        elif t.token_type in {TokenType.KNIT, 
                              TokenType.PURL, 
                              TokenType.KFB, 
                              TokenType.M1L, 
                              TokenType.M1R, 
                              TokenType.SSK, 
                              TokenType.K2TOG, 
                              TokenType.ID,
                              TokenType.LPAREN}:
            return self.parse_row_stmt()
        elif t.token_type == TokenType.WORK:
            return self.parse_work_stmt()
        elif t.token_type == TokenType.PRINT:
            return self.parse_print_stmt()
        else:
            self.syntax_error()
    
    def parse_cast_on_stmt(self) -> CastOnStmt:
        # cast_on_stmt → CAST_ON expr SEMICOLON
        self.consume(TokenType.CAST_ON)
        expr = self.parse_expr()
        self.consume(TokenType.SEMICOLON)
        return CastOnStmt(expr)
    
    def parse_bind_off_stmt(self) -> BindOffStmt:
        # bind_off_stmt → BIND_OFF expr SEMICOLON
        self.consume(TokenType.BIND_OFF)
        expr = self.parse_expr()
        self.consume(TokenType.SEMICOLON)
        return BindOffStmt(expr)
    
    def parse_repeat_block(self) -> RepeatStmt:
        # repeat_block → REPEAT expr LCBRAC pattern_body RCBRAC
        self.consume(TokenType.REPEAT)
        times = self.parse_expr()
        self.consume(TokenType.LCBRAC)
        body = self.parse_pattern_body()
        self.consume(TokenType.RCBRAC)
        return RepeatStmt(times, body)

    def parse_row_stmt(self) -> RowStatement:
        # row_stmt → motif_line_list fill_opt SEMICOLON
        elements = self.parse_motif_line_list()
        fill = self.parse_fill_opt()
        self.consume(TokenType.SEMICOLON)
        return RowStatement(elements, fill)
    
    def parse_print_stmt(self) -> PrintStmt:
        # print_stmt → PRINT LPAREN QUOTED_STRING RPAREN SEMICOLON
        self.consume(TokenType.PRINT)
        self.consume(TokenType.LPAREN)
        message = self.consume(TokenType.QUOTED_STRING).lexeme
        self.consume(TokenType.RPAREN)
        self.consume(TokenType.SEMICOLON)
        return PrintStmt(message)

    
    def parse_execute_stmt(self) -> PatternCall:
        # execute_stmt → EXECUTE LPAREN pattern_call RPAREN SEMICOLON
        self.consume(TokenType.EXECUTE)
        self.consume(TokenType.LPAREN)
        pattern_call = self.parse_pattern_call()
        self.consume(TokenType.RPAREN)
        self.consume(TokenType.SEMICOLON)
        return pattern_call
    
    def parse_fill_opt(self) -> bool:
        # fill_opt → fill | epsilon
        t = self.lexer.peek(1)
        if t.token_type == TokenType.FILL:
            self.consume(TokenType.FILL)
            return True
        elif t.token_type == TokenType.SEMICOLON:
            return False
        else:
            self.syntax_error()
    
    def parse_work_stmt(self) -> WorkStmt:
        # work_stmt → WORK LPAREN param_list RPAREN SEMICOLON
        self.consume(TokenType.WORK)
        self.consume(TokenType.LPAREN)
        pattern_name = self.consume(TokenType.ID).lexeme
        self.consume(TokenType.LPAREN)
        args = self.parse_param_list()
        self.consume(TokenType.RPAREN)
        self.consume(TokenType.RPAREN)
        self.consume(TokenType.SEMICOLON)
        return WorkStmt(pattern_name, args)
    
    def parse_pattern_call(self) -> PatternCall:
        # pattern_call → ID LPAREN arg_list RPAREN
        name = self.consume(TokenType.ID).lexeme
        self.consume(TokenType.LPAREN)
        args = self.parse_arg_list()
        self.consume(TokenType.RPAREN)
        return PatternCall(name, args)
    
    def parse_arg_list(self) -> Optional[List[Expr]]:
        # arg_list → arg | epsilon
        t = self.lexer.peek(1)
        if t.token_type == TokenType.NUM:
            return self.parse_arg()
        elif t.token_type == TokenType.RPAREN:
            return
        else:
            self.syntax_error()
    
    def parse_arg(self) -> Optional[List[Expr]]:
        # arg → factor COMMA arg | factor
        arg = self.parse_factor()
        t = self.lexer.peek(1)
        if t.token_type == TokenType.COMMA:
            self.consume(TokenType.COMMA)
            return [arg] + self.parse_arg()
        elif t.token_type == TokenType.RPAREN:
            return [arg]
        else:
            self.syntax_error()
    
    def parse_motif_line_list(self) -> List[Element]:
        # motif_line_list → element motif_line
        elements: List[Element] = []
        elements.append(self.parse_element())
        self.parse_motif_line(elements)
        return elements

    def parse_motif_line(self, elements: List[Element]):
        # motif_line → COMMA element motif_line | epsilon
        t = self.lexer.peek(1)
        if t.token_type == TokenType.COMMA:
            self.consume(TokenType.COMMA)
            elements.append(self.parse_element())
            self.parse_motif_line(elements)
        elif t.token_type in {TokenType.SEMICOLON, TokenType.RPAREN, TokenType.FILL}:
            return
        else:
            self.syntax_error()
    
    def parse_element(self) -> Element:
        # element → stitch_count | base_motif motif_repeat
        t = self.lexer.peek(1)

        if t.token_type in {TokenType.KNIT, 
                            TokenType.PURL, 
                            TokenType.KFB, 
                            TokenType.M1L, 
                            TokenType.M1R, 
                            TokenType.SSK, 
                            TokenType.K2TOG}:
            return self.parse_stitch_count()

        elif t.token_type in {TokenType.ID, TokenType.LPAREN}:
            motif = self.parse_base_motif()          # returns Motif
            repeat = self.parse_motif_repeat()       # returns Expr (default Num(1))
            return Element(motif=motif, repeat=repeat)

        else:
            self.syntax_error()


    def parse_stitch_count(self) -> Element:
        # stitch_count → stitch_operator expr | stitch_operator LBRAC expr RBRAC
        motif = self.parse_stitch_operator()

        if self.lexer.peek(1).token_type == TokenType.LBRAC:
            self.consume(TokenType.LBRAC)
            repeat = self.parse_expr()
            self.consume(TokenType.RBRAC)
        else:
            repeat = self.parse_expr()

        return Element(motif=motif, repeat=repeat)
    
    def parse_stitch_operator(self) -> StitchMotif:
        # stitch_operator → KNIT | PURL | KFB | M1L | M1R | SSK | K2TOG
        t = self.consume(
            {
                TokenType.KNIT,
                TokenType.PURL,
                TokenType.KFB,
                TokenType.M1L,
                TokenType.M1R,
                TokenType.SSK,
                TokenType.K2TOG,
            },
            context="stitch operator",
        )
        return StitchMotif(t.lexeme)
    
    def parse_base_motif(self) -> Motif:
        # base_motif → motif_ref | paren_motif 
        motif = Motif()
        t = self.lexer.peek(1)
        if t.token_type == TokenType.ID:
            motif = self.parse_motif_ref()
        elif t.token_type == TokenType.LPAREN:
            motif = self.parse_paren_motif()
        else:
            self.syntax_error()
        return motif
    
    def parse_motif_ref(self) -> RefMotif:
        # motif_ref → ID // references user defined stitch
        t = self.consume(TokenType.ID, context="motif reference")
        return RefMotif(t.lexeme)
    
    def parse_paren_motif(self) -> ParenMotif:
        # paren_motif → LPAREN motif_line_list RPAREN
        self.consume(TokenType.LPAREN)
        elements = self.parse_motif_line_list()
        self.consume(TokenType.RPAREN)
        return ParenMotif(elements=elements)
    
    def parse_motif_repeat(self) -> Optional[Expr]:
        # motif_repeat → MULT repeat_count | epsilon
        t = self.lexer.peek(1)
        if t.token_type == TokenType.MULT:
            self.consume(TokenType.MULT)
            return self.repeat_count()
        elif t.token_type in {TokenType.COMMA,
                              TokenType.RPAREN, 
                              TokenType.SEMICOLON, 
                              TokenType.FILL}:
            return Num(1)  # default repeat count is 1
        else:
            self.syntax_error()

    def repeat_count(self) -> Expr:
        # motif_repeat → MULT repeat_count | epsilon
        #repeat_count → NUM | ID | LPAREN expr RPAREN
        t = self.lexer.peek(1)

        if t.token_type == TokenType.NUM:
            tok = self.consume(TokenType.NUM)
            return Num(int(tok.lexeme))

        elif t.token_type == TokenType.ID:
            tok = self.consume(TokenType.ID)
            return Var(tok.lexeme)

        elif t.token_type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN)
            e = self.parse_expr()     # full expr allowed only if parenthesized
            self.consume(TokenType.RPAREN)
            return e

        else:
            self.syntax_error()

    def parse_expr(self) -> Expr:
        # expr → term expr_tail
        left = self.parse_term()
        return self.parse_expr_tail(left)
    
    def parse_term(self) -> Expr:
        # term → factor term_tail
        left = self.parse_factor()
        return self.parse_term_tail(left)


    def parse_factor(self) -> Expr:
        # factor → NUM | stitch_operator | ID | LPAREN expr RPAREN
        # might remove stitch_operator
        t = self.lexer.peek(1)
        if t.token_type == TokenType.NUM:
            return Num(int(self.consume(TokenType.NUM).lexeme))
        elif t.token_type == TokenType.ID:
            return Var(self.consume(TokenType.ID).lexeme)
        elif t.token_type == TokenType.LPAREN:
            self.consume(TokenType.LPAREN)
            expr = self.parse_expr()
            self.consume(TokenType.RPAREN)
            return expr
        else:
            self.syntax_error()
    
    def parse_expr_tail(self, left: Expr) -> Expr:
        # expr_tail → add_operator term expr_tail | epsilon
        t = self.lexer.peek(1)
        if t.token_type in {TokenType.PLUS, TokenType.MINUS}:
            op = self.parse_add_operator()     # "+" or "-"
            right = self.parse_term()
            combined = BinOp(op, left, right)
            return self.parse_expr_tail(combined)
        elif t.token_type in {
            TokenType.SEMICOLON,
            TokenType.COMMA,
            TokenType.RPAREN,
            TokenType.LCBRAC,  # <-- needed for repeat expr {
            TokenType.RBRAC,   # <-- needed for stitch_operator [ expr ]
            TokenType.FILL,    # <-- row_stmt: ... fill ;
        }:
            return left
        else:
            self.syntax_error()

    def parse_term_tail(self, left: Expr) -> Expr:
        # term_tail → MULT factor | epsilon
        t = self.lexer.peek(1)

        if t.token_type == TokenType.MULT:
            self.consume(TokenType.MULT)
            right = self.parse_factor()
            combined = BinOp("*", left, right)
            return self.parse_term_tail(combined)  # recurse to allow a*b*c

        elif t.token_type in {
            TokenType.SEMICOLON,
            TokenType.COMMA,
            TokenType.RPAREN,
            TokenType.LCBRAC,
            TokenType.RBRAC,
            TokenType.FILL,
            TokenType.PLUS,
            TokenType.MINUS,
        }:
            return left

        else:
            self.syntax_error()
    
    def parse_add_operator(self) -> str:
        # add_operator → PLUS | MINUS
        t = self.consume({TokenType.PLUS, TokenType.MINUS}, context="add operator")
        return "+" if t.token_type == TokenType.PLUS else "-"
    


# program             → stitch_def_list pattern_list execute_stmt EOF
# stitch_def_list    → stitch_def stitch_def_list | epsilon
# stitch_def           → STITCH ID EQUALS motif_line_list SEMICOLON 
# pattern_list	→ pattern pattern_list | epsilon
# pattern		→ PATTERN ID LPAREN param_header RPAREN LCBRAC pattern_body RCBRAC
# param_header   → param_list  |  epsilon
# param_list	→ ID COMMA param_list | ID
# pattern_body	→ pattern_stmt pattern_body | pattern_stmt
# pattern_stmt 	→ cast_on_stmt | bind_off_stmt | repeat_block | row_stmt | work_stmt | print_stmt
# cast_on_stmt	→ CAST_ON expr SEMICOLON
# bind_off_stmt    → BIND_OFF expr SEMICOLON
# repeat_block     →  REPEAT expr LCBRAC pattern_body RCBRAC
# row_stmt	→ motif_line_list fill_opt SEMICOLON
# fill_opt               → fill | epsilon
# work_stmt	→ WORK LPAREN pattern_call RPAREN SEMICOLON
# pattern_call       → ID LPAREN arg_list RPAREN
# arg_list		→  arg |  epsilon
# arg	             →  NUM COMMA arg | NUM
# execute_stmt     → EXECUTE LPAREN pattern_call RPAREN SEMICOLON
# print_stmt	→ PRINT LPAREN QUOTED_STRING RPAREN SEMICOLON
# motif_line_list   → element motif_line
# motif_line          → COMMA element motif_line | epsilon
# element              → stitch_count  | base_motif motif_repeat
# base_motif         → motif_ref | paren_motif
# motif_ref            → ID // references user defined stitch
# paren_motif       → LPAREN motif_line_list RPAREN
# motif_repeat    → MULT expr | epsilon
# stitch_count       → stitch_operator expr | stitch_operator LBRAC expr RBRAC
# expr		→ term expr_tail
# expr_tail             → add_operator term expr_tail | epsilon
# add_operator     → PLUS | MINUS
# term                   → factor term_tail
# term_tail            → MULT factor term_tail | epsilon
# factor 		→ NUM | ID | LPAREN expr RPAREN
# stitch_operator  → KNIT | PURL | KFB | M1L | M1R | SSK | K2TOG


    
if __name__ == "__main__":
    import sys
    from input_buffer import InputBuffer
    from lexer import Lexer

    if len(sys.argv) != 2:
        print("Usage: python3 parser.py <file>")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        ib = InputBuffer(f)
        lexer = Lexer(ib)
        parser = Parser(lexer)
        program = parser.parse_input()
        interpreter = Interpreter(program)
        output = interpreter.run_program()
        for line in output:
            print(line)

    print("Parse OK")

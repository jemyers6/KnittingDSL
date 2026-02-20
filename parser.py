from __future__ import annotations
from lexer import Lexer, Token, TokenType
import sys
from dataclasses import dataclass, field
from typing import List, Optional

class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer

    def syntax_error(self):
        print("SYNTAX ERROR")
        sys.exit(0)

    def expect(self, expected_type):
        token = self.lexer.get_token()
        if token.token_type != expected_type:
            raise SyntaxError(f"Expected token of type {expected_type}, got {token.token_type}")
        return token
    
    def parse_input(self):
        self.parse_program()
        self.expect(TokenType.EOF)

    def parse_program(self):
        # program  → stitch_def_list pattern_list execute_stmt
        self.parse_stitch_def_list()
        self.parse_pattern_list()
        self.parse_execute_stmt()


    def parse_stitch_def_list(self):
        # stitch_def_list → stitch_def stitch_def_list | epsilon
        t = self.lexer.peek(1)
        if t.token_type == TokenType.STITCH:
            self.parse_stitch_def()
            self.parse_stitch_def_list()
        elif t.token_type in {TokenType.PATTERN, TokenType.EXECUTE}:
            return
        else:
            self.syntax_error()
    
    def parse_stitch_def(self):
        # stitch_def → STITCH ID EQUALS motif_line_list SEMICOLON 
        self.expect(TokenType.STITCH)
        self.expect(TokenType.ID)
        self.expect(TokenType.EQUALS)
        self.parse_motif_line_list()
        self.expect(TokenType.SEMICOLON)
    
    def parse_pattern_list(self):
        # pattern_list → pattern pattern_list | epsilon
        t = self.lexer.peek(1)
        if t.token_type == TokenType.PATTERN:
            self.parse_pattern()
            self.parse_pattern_list()
        elif t.token_type == TokenType.EXECUTE:
            return
        else:
            self.syntax_error()

    def parse_pattern(self):
        # pattern → PATTERN ID LPAREN param_header RPAREN LCBRAC pattern_body RCBRAC
        self.expect(TokenType.PATTERN)
        self.expect(TokenType.ID)
        self.expect(TokenType.LPAREN)
        self.parse_param_header()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LCBRAC)
        self.parse_pattern_body()
        self.expect(TokenType.RCBRAC)

    def parse_param_header(self):
        # param_header → param_list | epsilon
        t = self.lexer.peek(1)
        if t.token_type == TokenType.ID:
            self.parse_param_list()
        elif t.token_type == TokenType.RPAREN:
            return
        else:
            self.syntax_error()

    def parse_param_list(self):
        # param_list → ID COMMA param_list | ID
        self.expect(TokenType.ID)
        t = self.lexer.peek(1)
        if t.token_type == TokenType.COMMA:
            self.expect(TokenType.COMMA)
            self.parse_param_list()
        elif t.token_type == TokenType.RPAREN:
            return
        else:
            self.syntax_error()
    
    def parse_pattern_body(self):
        # pattern_body → pattern_stmt pattern_body | pattern_stmt
        self.parse_pattern_stmt()
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
            self.parse_pattern_body()
        elif t.token_type == TokenType.RCBRAC:
            return
        else:
            self.syntax_error()

    def parse_pattern_stmt(self):
        # pattern_stmt → cast_on_stmt | bind_off_stmt | repeat_block | row_stmt | work_stmt | print_stmt
        t = self.lexer.peek(1)
        if t.token_type == TokenType.CAST_ON:
            self.parse_cast_on_stmt()
        elif t.token_type == TokenType.BIND_OFF:
            self.parse_bind_off_stmt()
        elif t.token_type == TokenType.REPEAT:
            self.parse_repeat_block()
        elif t.token_type in {TokenType.KNIT, 
                              TokenType.PURL, 
                              TokenType.KFB, 
                              TokenType.M1L, 
                              TokenType.M1R, 
                              TokenType.SSK, 
                              TokenType.K2TOG, 
                              TokenType.ID}:
            self.parse_row_stmt()
        elif t.token_type == TokenType.WORK:
            self.parse_work_stmt()
        elif t.token_type == TokenType.PRINT:
            self.parse_print_stmt()
        else:
            self.syntax_error()
    
    def parse_cast_on_stmt(self):
        # cast_on_stmt → CAST_ON expr SEMICOLON
        self.expect(TokenType.CAST_ON)
        self.parse_expr()
        self.expect(TokenType.SEMICOLON)
    
    def parse_bind_off_stmt(self):
        # bind_off_stmt → BIND_OFF expr SEMICOLON
        self.expect(TokenType.BIND_OFF)
        self.parse_expr()
        self.expect(TokenType.SEMICOLON)
    
    def parse_repeat_block(self):
        # repeat_block → REPEAT expr LCBRAC pattern_body RCBRAC
        self.expect(TokenType.REPEAT)
        self.parse_expr()
        self.expect(TokenType.LCBRAC)
        self.parse_pattern_body()
        self.expect(TokenType.RCBRAC)

    def parse_row_stmt(self):
        # row_stmt → motif_line_list fill_opt SEMICOLON
        self.parse_motif_line_list()
        self.parse_fill_opt()
        self.expect(TokenType.SEMICOLON)
    
    def parse_print_stmt(self):
        # print_stmt → PRINT LPAREN QUOTED_STRING RPAREN SEMICOLON
        self.expect(TokenType.PRINT)
        self.expect(TokenType.LPAREN)
        self.expect(TokenType.QUOTED_STRING)
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
    
    def parse_execute_stmt(self):
        # execute_stmt → EXECUTE LPAREN pattern_call RPAREN SEMICOLON
        self.expect(TokenType.EXECUTE)
        self.expect(TokenType.LPAREN)
        self.parse_pattern_call()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
    
    def parse_fill_opt(self):
        # fill_opt → fill | epsilon
        t = self.lexer.peek(1)
        if t.token_type == TokenType.FILL:
            self.expect(TokenType.FILL)
        elif t.token_type == TokenType.SEMICOLON:
            return
        else:
            self.syntax_error()
    
    def parse_work_stmt(self):
        # work_stmt → WORK LPAREN pattern_call RPAREN SEMICOLON
        self.expect(TokenType.WORK)
        self.expect(TokenType.LPAREN)
        self.expect(TokenType.ID)
        self.expect(TokenType.LPAREN)
        self.parse_param_list()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
    
    def parse_pattern_call(self):
        # pattern_call → ID LPAREN arg_list RPAREN
        self.expect(TokenType.ID)
        self.expect(TokenType.LPAREN)
        self.parse_arg_list()
        self.expect(TokenType.RPAREN)
    
    def parse_arg_list(self):
        # arg_list → arg | epsilon
        t = self.lexer.peek(1)
        if t.token_type == TokenType.NUM:
            self.parse_arg()
        elif t.token_type == TokenType.RPAREN:
            return
        else:
            self.syntax_error()

    def parse_arg(self):
        # arg → NUM COMMA arg | NUM
        self.expect(TokenType.NUM)
        t = self.lexer.peek(1)
        if t.token_type == TokenType.COMMA:
            self.expect(TokenType.COMMA)
            self.parse_arg()
        elif t.token_type == TokenType.RPAREN:
            return
        else:
            self.syntax_error()
    
    def parse_motif_line_list(self):
        # motif_line_list → element motif_line
        self.parse_element()
        self.parse_motif_line()

    def parse_motif_line(self):
        # motif_line → COMMA element motif_line | epsilon
        t = self.lexer.peek(1)
        if t.token_type == TokenType.COMMA:
            self.expect(TokenType.COMMA)
            self.parse_element()
            self.parse_motif_line()
        elif t.token_type in {TokenType.SEMICOLON, TokenType.RPAREN, TokenType.FILL}:
            return
        else:
            self.syntax_error()
    
    def parse_element(self):
        # element → stitch_count | base_motif motif_repeat
        t = self.lexer.peek(1)
        if t.token_type in {TokenType.KNIT, 
                            TokenType.PURL, 
                            TokenType.KFB, 
                            TokenType.M1L, 
                            TokenType.M1R, 
                            TokenType.SSK, 
                            TokenType.K2TOG}:
            self.parse_stitch_count()
        elif t.token_type == TokenType.ID or t.token_type == TokenType.LPAREN:
            self.parse_base_motif()
            self.parse_motif_repeat()
        elif t.token_type in {TokenType.SEMICOLON, TokenType.RPAREN, TokenType.FILL}:
            return
        else:
            self.syntax_error()


    def parse_stitch_count(self):
        # stitch_count → stitch_operator expr | stitch_operator LBRAC expr RBRAC
        self.parse_stitch_operator()
        t = self.lexer.peek(1)
        if t.token_type == TokenType.LBRAC:
            self.expect(TokenType.LBRAC)
            self.parse_expr()
            self.expect(TokenType.RBRAC)
        else:
            self.parse_expr()
    
    def parse_stitch_operator(self):
        # stitch_operator → KNIT | PURL | KFB | M1L | M1R | SSK | K2TOG
        t = self.lexer.get_token()
        if t.token_type not in {TokenType.KNIT, 
                                TokenType.PURL, 
                                TokenType.KFB, 
                                TokenType.M1L, 
                                TokenType.M1R, 
                                TokenType.SSK, 
                                TokenType.K2TOG}:
            self.syntax_error()
    
    def parse_base_motif(self):
        # base_motif → motif_ref | paren_motif 
        t = self.lexer.peek(1)
        if t.token_type == TokenType.ID:
            self.parse_motif_ref()
        elif t.token_type == TokenType.LPAREN:
            self.parse_paren_motif()
        else:
            self.syntax_error()
    
    def parse_motif_ref(self):
        # motif_ref → ID // references user defined stitch
        self.expect(TokenType.ID)
    
    def parse_paren_motif(self):
        # paren_motif → LPAREN motif_line_list RPAREN
        self.expect(TokenType.LPAREN)
        self.parse_motif_line_list()
        self.expect(TokenType.RPAREN)
    
    def parse_motif_repeat(self):
        # motif_repeat → MULT repeat_count | epsilon
        t = self.lexer.peek(1)
        if t.token_type == TokenType.MULT:
            self.expect(TokenType.MULT)
            self.repeat_count()
        elif t.token_type in {TokenType.COMMA,
                              TokenType.RPAREN, 
                              TokenType.SEMICOLON, 
                              TokenType.FILL}:
            return
        else:
            self.syntax_error()

    def repeat_count(self):
        # motif_repeat → MULT repeat_count | epsilon
        #repeat_count → NUM | ID | LPAREN expr RPAREN
        t = self.lexer.peek(1)
        if t.token_type == TokenType.NUM:
            self.expect(TokenType.NUM)
        elif t.token_type == TokenType.ID:
            self.expect(TokenType.ID)
        elif t.token_type == TokenType.LPAREN:
            self.expect(TokenType.LPAREN)
            self.parse_expr()
            self.expect(TokenType.RPAREN)
        else:
            self.syntax_error()

    def parse_expr(self):
        # expr → term expr_tail
        self.parse_term()
        self.parse_expr_tail()
    
    def parse_term(self):
        # term → factor term_tail
        self.parse_factor()
        self.parse_term_tail()


    def parse_factor(self):
        # factor → NUM | stitch_operator | ID | LPAREN expr RPAREN
        # might remove stitch_operator
        t = self.lexer.peek(1)
        if t.token_type == TokenType.NUM:
            self.expect(TokenType.NUM)
        elif t.token_type in {TokenType.KNIT, 
                              TokenType.PURL, 
                              TokenType.KFB, 
                              TokenType.M1L, 
                              TokenType.M1R, 
                              TokenType.SSK, 
                              TokenType.K2TOG}:
            self.parse_stitch_operator()
        elif t.token_type == TokenType.ID:
            self.expect(TokenType.ID)
        elif t.token_type == TokenType.LPAREN:
            self.expect(TokenType.LPAREN)
            self.parse_expr()
            self.expect(TokenType.RPAREN)
        else:
            self.syntax_error()
    
    def parse_expr_tail(self):
        # expr_tail → add_operator term expr_tail | epsilon
        t = self.lexer.peek(1)
        if t.token_type in {TokenType.PLUS, TokenType.MINUS}:
            self.parse_add_operator()
            self.parse_term()
            self.parse_expr_tail()
        elif t.token_type in {
            TokenType.SEMICOLON,
            TokenType.COMMA,
            TokenType.RPAREN,
            TokenType.LCBRAC,  # <-- needed for repeat expr {
            TokenType.RBRAC,   # <-- needed for stitch_operator [ expr ]
            TokenType.FILL,    # <-- row_stmt: ... fill ;
        }:
            return
        else:
            self.syntax_error()

    def parse_term_tail(self):
        # term_tail → MULT factor | epsilon
        t = self.lexer.peek(1)
        if t.token_type == TokenType.MULT:
            self.expect(TokenType.MULT)
            self.parse_factor()
        elif t.token_type in {
            TokenType.SEMICOLON,
            TokenType.COMMA,
            TokenType.RPAREN,
            TokenType.LCBRAC,  # <-- needed for repeat expr {
            TokenType.RBRAC,   # <-- needed for stitch_operator [ expr ]
            TokenType.FILL,    # <-- row_stmt: ... fill ;
            TokenType.PLUS, TokenType.MINUS
        }:
            return
        else:
            self.syntax_error()
    
    def parse_add_operator(self):
        # add_operator → PLUS | MINUS
        t = self.lexer.get_token()
        if t.token_type not in {TokenType.PLUS, TokenType.MINUS}:
            self.syntax_error()
    


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
# factor 		→ NUM | stitch_operator | ID | LPAREN expr RPAREN
# stitch_operator  → KNIT | PURL | KFB | M1L | M1R | SSK | K2TOG


    
if __name__ == "__main__":
    import sys
    from inputbuf import InputBuffer
    from lexer import Lexer

    if len(sys.argv) != 2:
        print("Usage: python3 parser.py <file>")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        ib = InputBuffer(f)
        lexer = Lexer(ib)
        parser = Parser(lexer)
        parser.parse_input()

    print("Parse OK")

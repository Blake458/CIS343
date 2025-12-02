# Recursive Descent Parser for Sloth Programming Language
# by Blake Collins
#
# This module implements a recursive descent parser that converts a sequence 
# of tokens into an Abstract Syntax Tree (AST) following Sloth's grammar rules.
#
# Grammar hierarchy (lowest to highest precedence):
#     1. Expression (assignment)
#     2. Equality (==, !=)
#     3. Comparison (<, <=, >, >=)
#     4. Term (+, -)
#     5. Factor (*, /)
#     6. Unary (!, -)
#     7. Call (function calls, property access)
#     8. Primary (literals, identifiers, grouping)

from error_handler import *
from custom_token import *
from expression import *
from statement import *

class Parser:
    # Recursive descent parser that maps a sequence of tokens into an AST.
    # Uses the visitor pattern for traversing and constructing the syntax tree.

    def __init__(self, tokens):
        # Initialize the parser with a list of tokens.
        self.tokens = tokens
        self.current = 0
        self.ast = self.parse()

    # ============================================================================
    # MAIN PARSING ENTRY POINT
    # ============================================================================

    def parse(self):
        # Parse all tokens into a list of statements (AST).
        # Returns list of parsed statements, or empty list if error occurs.
        statements = []
        try:
            while not self.is_at_end():
                stmt = self.declaration()
                if stmt:  # Only add non-None statements
                    statements.append(stmt)
            return statements
        except ParseError:
            self.synchronize()
            return []
        except RuntimeError as error:
            print(f"[Runtime Error] {error}")
            return []

    # ============================================================================
    # DECLARATIONS (Top-level constructs)
    # ============================================================================

    def declaration(self):
        # Parse declarations (classes, functions, variables) and statements.
        try:
            if self.match(TokenValue.SLOTH):
                return self.sloth_declaration()
            if self.match(TokenValue.FUN):
                return self.fun_declaration()
            if self.match(TokenValue.NEW):
                return self.var_declaration()
            return self.statement()
        except ParseError:
            self.synchronize()
            return None

    def var_declaration(self):
        # Parse variable declarations: 'new var_name = expression;'
        name = self.consume(TokenValue.IDENTIFIER, "Expect variable name.")

        initializer = None
        if self.match(TokenValue.EQUAL):
            initializer = self.expression()

        self.consume(TokenValue.SEMICOLON, "Expect ';' after variable declaration.")
        return VarStmt(name.lexeme, initializer)

    def fun_declaration(self):
        # Parse function declarations: 'fun name(params) { body }'
        name = self.consume(TokenValue.IDENTIFIER, "Expect function name.")
        self.consume(TokenValue.LEFT_PAREN, "Expect '(' after function name.")
        
        # Parse parameters
        params = []
        if not self.check(TokenValue.RIGHT_PAREN):
            while True:
                if len(params) >= 255:
                    self.error(self.peek(), "Cannot have more than 255 parameters.")
                params.append(self.consume(TokenValue.IDENTIFIER, "Expect parameter name."))
                if not self.match(TokenValue.COMMA):
                    break

        self.consume(TokenValue.RIGHT_PAREN, "Expect ')' after parameters.")
        self.consume(TokenValue.LEFT_BRACE, "Expect '{' before function body.")
        body = Block(self.block())
        return Function(name.lexeme, params, body)

    def sloth_declaration(self):
        # Parse class declarations: 'sloth Name < SuperClass { methods }'
        name = self.consume(TokenValue.IDENTIFIER, "Expect sloth name.")

        # Handle inheritance
        supersloth = None
        if self.match(TokenValue.LESS):
            self.consume(TokenValue.IDENTIFIER, "Expect supersloth name.")
            supersloth = Variable(self.previous().lexeme)

        self.consume(TokenValue.LEFT_BRACE, "Expect '{' before sloth body.")

        # Parse methods
        methods = []
        while not self.check(TokenValue.RIGHT_BRACE) and not self.is_at_end():
            methods.append(self.fun_declaration())

        self.consume(TokenValue.RIGHT_BRACE, "Expect '}' after sloth body.")
        return SlothStmt(name.lexeme, supersloth, methods)

    # ============================================================================
    # STATEMENTS
    # ============================================================================

    def statement(self):
        # Parse various statement types.
        if self.match(TokenValue.PRINT):
            return self.print_statement()
        if self.match(TokenValue.IF):
            return self.if_statement()
        if self.match(TokenValue.WHILE):
            return self.while_statement()
        if self.match(TokenValue.FOR):
            return self.for_statement()
        if self.match(TokenValue.LEFT_BRACE):
            return Block(self.block())
        if self.match(TokenValue.GIVE):
            return self.return_statement()
        
        return self.expression_statement()

    def return_statement(self):
        # Parse return statements: 'give expression;'
        keyword = self.previous()
        value = None
        if not self.check(TokenValue.SEMICOLON):
            value = self.expression()
        self.consume(TokenValue.SEMICOLON, "Expect ';' after return value.")
        return ReturnStmt(keyword, value)

    def print_statement(self):
        # Parse print statements: 'print expression;'
        value = self.expression()
        self.consume(TokenValue.SEMICOLON, "Expect ';' after value.")
        return PrintStmt(value)

    def expression_statement(self):
        # Parse expression statements: 'expression;'
        expr = self.expression()
        self.consume(TokenValue.SEMICOLON, "Expect ';' after expression.")
        return ExpressionStmt(expr)

    def if_statement(self):
        # Parse if statements: 'if (condition) { then_branch } else { else_branch }'
        self.consume(TokenValue.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self.expression()
        self.consume(TokenValue.RIGHT_PAREN, "Expect ')' after if condition.")

        # Require braces for then branch
        if not self.match(TokenValue.LEFT_BRACE):
            self.error(self.peek(), "Expected '{' after if condition.")
        then_branch = Block(self.block())

        # Validate block contents
        self._validate_block(then_branch, "if")

        # Parse optional else branch
        else_branch = None
        if self.match(TokenValue.ELSE):
            if not self.match(TokenValue.LEFT_BRACE):
                self.error(self.peek(), "Expected '{' after else.")
            else_branch = Block(self.block())
            self._validate_block(else_branch, "else")

        return IfStmt(condition, then_branch, else_branch)

    def while_statement(self):
        # Parse while loops: 'while (condition) { body }'
        self.consume(TokenValue.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self.expression()
        self.consume(TokenValue.RIGHT_PAREN, "Expect ')' after while condition.")

        # Require braces for loop body
        if not self.match(TokenValue.LEFT_BRACE):
            self.error(self.peek(), "Expected '{' after while condition.")
        body = Block(self.block())

        self._validate_block(body, "while")
        return WhileStmt(condition, body)

    def for_statement(self):
        # Parse for loops: 'for (init; condition; increment) { body }'
        self.consume(TokenValue.LEFT_PAREN, "Expect '(' after 'for'.")

        # Parse initializer
        if self.match(TokenValue.SEMICOLON):
            initializer = None
        elif self.match(TokenValue.NEW):
            initializer = self.var_declaration()
        else:
            initializer = self.expression_statement()

        # Parse condition
        condition = None
        if not self.check(TokenValue.SEMICOLON):
            condition = self.expression()
        self.consume(TokenValue.SEMICOLON, "Expect ';' after loop condition.")

        # Parse increment
        increment = None
        if not self.check(TokenValue.RIGHT_PAREN):
            increment = self.expression()
        self.consume(TokenValue.RIGHT_PAREN, "Expect ')' after for clauses.")

        # Parse body
        if not self.match(TokenValue.LEFT_BRACE):
            self.error(self.peek(), "Expected '{' after for clauses.")
        body = Block(self.block())

        self._validate_block(body, "for")
        return ForStmt(initializer, condition, increment, body)

    def block(self):
        # Parse a block of statements delimited by { }.
        statements = []
        while not self.check(TokenValue.RIGHT_BRACE) and not self.is_at_end():
            stmt = self.declaration()
            if stmt:  # Only add non-None statements
                statements.append(stmt)

        self.consume(TokenValue.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    # ============================================================================
    # EXPRESSIONS (by precedence, lowest to highest)
    # ============================================================================

    def expression(self):
        # Parse expressions starting with assignment.
        return self.assignment()

    def assignment(self):
        # Parse assignment expressions: 'target = value'
        expr = self.equality()

        if self.match(TokenValue.EQUAL):
            equals = self.previous()
            value = self.assignment()  # Right-associative

            if isinstance(expr, Variable):
                return Assign(expr.name, value)
            elif isinstance(expr, Get):
                return Set(expr.object, expr.name, value)
            
            self.error(equals, "Invalid assignment target.")

        return expr

    def equality(self):
        # Parse equality expressions (==, !=).
        left = self.comparison()

        while self.match(TokenValue.EQUAL_EQUAL, TokenValue.BANG_EQUAL):
            operator = self.previous()
            right = self.comparison()
            left = Binary(left, operator, right)

        return left

    def comparison(self):
        # Parse comparison expressions (<, <=, >, >=).
        left = self.term()

        while self.match(TokenValue.GREATER, TokenValue.GREATER_EQUAL,
                         TokenValue.LESS, TokenValue.LESS_EQUAL):
            operator = self.previous()
            right = self.term()
            left = Binary(left, operator, right)

        return left

    def term(self):
        # Parse addition and subtraction expressions (+, -).
        left = self.factor()

        while self.match(TokenValue.MINUS, TokenValue.PLUS):
            operator = self.previous()
            right = self.factor()
            left = Binary(left, operator, right)

        return left

    def factor(self):
        # Parse multiplication and division expressions (*, /).
        left = self.unary()

        while self.match(TokenValue.SLASH, TokenValue.STAR):
            operator = self.previous()
            right = self.unary()
            left = Binary(left, operator, right)

        return left

    def unary(self):
        # Parse unary expressions (!, -).
        if self.match(TokenValue.BANG, TokenValue.MINUS):
            operator = self.previous()
            right = self.unary()
            return Unary(operator, right)

        return self.call()

    def call(self):
        # Parse function calls and property access: 'expr(args)' or 'expr.property'
        expr = self.primary()

        while True:
            if self.match(TokenValue.LEFT_PAREN):
                expr = self.finish_call(expr)
            elif self.match(TokenValue.DOT):
                name = self.consume(TokenValue.IDENTIFIER, "Expect property name after '.'.")
                expr = Get(expr, name)
            else:
                break

        return expr

    def primary(self):
        # Parse primary expressions (literals, identifiers, grouping, this, super).
        
        # Literals
        if self.match(TokenValue.FALSE):
            return Literal(False)
        if self.match(TokenValue.TRUE):
            return Literal(True)
        if self.match(TokenValue.NULL):
            return Literal(None)
        if self.match(TokenValue.NUMBER, TokenValue.STRING):
            return Literal(self.previous().literal)

        # Special keywords
        if self.match(TokenValue.THIS):
            return This(self.previous())
        if self.match(TokenValue.SUPER):
            keyword = self.previous()
            self.consume(TokenValue.DOT, "Expect '.' after 'super'.")
            method = self.consume(TokenValue.IDENTIFIER, "Expect supersloth method name.")
            return SuperSloth(keyword, method)

        # Identifiers
        if self.match(TokenValue.IDENTIFIER):
            return Variable(self.previous().lexeme)

        # Grouping
        if self.match(TokenValue.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenValue.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)

        self.error(self.peek(), "Expect expression.")

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def finish_call(self, callee):
        # Parse function call arguments.
        arguments = []
        if not self.check(TokenValue.RIGHT_PAREN):
            while True:
                if len(arguments) >= 255:
                    self.error(self.peek(), "Can't have more than 255 arguments.")
                arguments.append(self.expression())
                if not self.match(TokenValue.COMMA):
                    break

        paren = self.consume(TokenValue.RIGHT_PAREN, "Expect ')' after arguments.")
        return Call(callee, paren, arguments)

    def _validate_block(self, block, context):
        # Validate that a block doesn't contain only a single variable declaration.
        if len(block.statements) == 1 and isinstance(block.statements[0], VarStmt):
            self.error(self.previous(), 
                      f"A {context} block containing only a single variable declaration is not allowed.")

    # ============================================================================
    # TOKEN NAVIGATION AND ERROR HANDLING
    # ============================================================================

    def synchronize(self):
        # Recover from parse errors by advancing to the next statement boundary.
        self.advance()
        while not self.is_at_end():
            if self.previous().type == TokenValue.SEMICOLON:
                return

            # Synchronize on statement keywords
            if self.match(TokenValue.SLOTH, TokenValue.FUN, TokenValue.NEW,
                         TokenValue.FOR, TokenValue.IF, TokenValue.WHILE,
                         TokenValue.PRINT, TokenValue.GIVE):
                return
            self.advance()

    def consume(self, token_type, message):
        # Consume a token of the expected type or raise an error.
        if self.check(token_type):
            return self.advance()
        raise self.error(self.peek(), message)

    def match(self, *types):
        # Check if current token matches any given type and consume if so.
        for token_type in types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def check(self, token_type):
        # Check if current token is of given type without consuming.
        return self.peek().type == token_type

    def advance(self):
        # Consume current token and return it.
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self):
        # Check if parser has reached end of tokens.
        return self.peek().type == TokenValue.EOF

    def peek(self):
        # Get current token without consuming it.
        if self.current >= len(self.tokens):
            return Token(TokenValue.EOF, "", None, self.current)
        return self.tokens[self.current]

    def previous(self):
        # Get the most recently consumed token.
        return self.tokens[self.current - 1]

    def error(self, token, message):
        # Report a parsing error and raise ParseError.
        ErrorHandler.error(token, message)
        raise ParseError(token, message)

    def __str__(self):
        # String representation for debugging.
        return f"Parser(current={self.current}, tokens={len(self.tokens)})"

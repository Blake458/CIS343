from error_handler import *
from custom_token import *
from expression import *
from statement import *


class Parser:
    """
    Recursive descent parser that maps a sequence of tokens
    into an Abstract Syntax Tree (AST).

    Order of operations:
        1 Expression
        2 Equality
        3 Comparison
        4 Term
        5 Factor
        6 Unary
        7 Primary
    """

    def __init__(self, tokens):
        """
        Initialize the parser.

        Args:
            tokens (list[Token]): The list of tokens from the scanner.
        """
        self.tokens = tokens
        self.current = 0
        self.ast = self.parse()

    def parse(self):
        """
        Start parsing the tokens and produce an AST.

        Returns:
            Expression | None: The root of the AST if parsing succeeds,
                               None if a ParseError occurs.
        """
        statements = []
        try:
            while not self.is_at_end():
                statements.append(self.declaration())
            return statements
        except ParseError:
            self.synchronize()
            return []
        except RuntimeError as error:
            print(f"[Runtime Error] {error}")
            return []
        
    def declaration(self):
        try:
            if self.match(TokenValue.FUN):
                return self.fun_declaration()   # <-- call fun_declaration, not function()

            if self.match(TokenValue.NEW):
                return self.var_declaration()

            return self.statement()
        except ParseError:
            self.synchronize()
            return None


    def var_declaration(self):
        """Parse new var_name = expression'"""
        name = self.consume(TokenValue.IDENTIFIER, "Expect variable name.")

        initializer = None
        if self.match(TokenValue.EQUAL):
            initializer = self.expression()

        self.consume(TokenValue.SEMICOLON, "Expect ';' after variable declaration.")
        return VarStmt(name.lexeme, initializer)
    

    def fun_declaration(self):
        name = self.consume(TokenValue.IDENTIFIER, "Expect function name.")
        self.consume(TokenValue.LEFT_PAREN, "Expect '(' after function name.")
        
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


    def statement(self):
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
        keyword = self.previous()
        value = None
        if not self.check(TokenValue.SEMICOLON):
            value = self.expression()
        self.consume(TokenValue.SEMICOLON, "Expect ';' after return value.")
        return ReturnStmt(keyword, value)



    def print_statement(self):
        value = self.expression()
        self.consume(TokenValue.SEMICOLON, "Expect ';' after value.")
        return PrintStmt(value)


    def expression_statement(self):
        expr = self.expression()
        self.consume(TokenValue.SEMICOLON, "Expect ';' after expression.")
        return ExpressionStmt(expr)
    

    def if_statement(self):
        self.consume(TokenValue.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self.expression()
        self.consume(TokenValue.RIGHT_PAREN, "Expect ')' after if condition.")

        if not self.match(TokenValue.LEFT_BRACE):
            self.error(self.peek(), "Expected '{' after if condition.")
        then_branch = Block(self.block())

        if len(then_branch.statements) == 1 and isinstance(then_branch.statements[0], VarStmt):
            self.error(self.previous(), "A block containing only a single variable declaration is not allowed.")

        else_branch = None
        if self.match(TokenValue.ELSE):
            if not self.match(TokenValue.LEFT_BRACE):
                self.error(self.peek(), "Expected '{' after else.")
            else_branch = Block(self.block())

            if len(else_branch.statements) == 1 and isinstance(else_branch.statements[0], VarStmt):
                self.error(self.previous(), "A block containing only a single variable declaration is not allowed.")

        return IfStmt(condition, then_branch, else_branch)


    def while_statement(self):
        self.consume(TokenValue.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self.expression()
        self.consume(TokenValue.RIGHT_PAREN, "Expect ')' after while condition.")

        # Require block for the loop body
        if not self.match(TokenValue.LEFT_BRACE):
            self.error(self.peek(), "Expected '{' after while condition.")
        body = Block(self.block())

        if len(body.statements) == 1 and isinstance(body.statements[0], VarStmt):
            self.error(self.previous(), "A block containing only a single variable declaration is not allowed.")

        return WhileStmt(condition, body)
    

    def for_statement(self):
        self.consume(TokenValue.LEFT_PAREN, "Expect '(' after 'for'.")

        # --- Initializer ---
        if self.match(TokenValue.SEMICOLON):
            initializer = None
        elif self.match(TokenValue.NEW):
            initializer = self.var_declaration()
        else:
            initializer = self.expression_statement()

        # --- Condition ---
        condition = None
        if not self.check(TokenValue.SEMICOLON):
            condition = self.expression()
        self.consume(TokenValue.SEMICOLON, "Expect ';' after loop condition.")

        # --- Increment ---
        increment = None
        if not self.check(TokenValue.RIGHT_PAREN):
            increment = self.expression()
        self.consume(TokenValue.RIGHT_PAREN, "Expect ')' after for clauses.")

        # --- Body ---
        if not self.match(TokenValue.LEFT_BRACE):
            self.error(self.peek(), "Expected '{' after for clauses.")
        body = Block(self.block())

        # --- Prevent single-var-only block ---
        if len(body.statements) == 1 and isinstance(body.statements[0], VarStmt):
            self.error(self.previous(), "A block containing only a single variable declaration is not allowed.")

        return ForStmt(initializer, condition, increment, body)


    def block(self):
        """Parse a block of statements delimited by { }."""
        statements = []
        while not self.check(TokenValue.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.declaration())

        self.consume(TokenValue.RIGHT_BRACE, "Expect '}' after block.")
        return statements



    def expression(self):
        """
        Parse an expression.

        Returns:
            Expression: The parsed equality expression.
        """
        return self.assignment()
    
    def assignment(self):
        expr = self.equality()

        if self.match(TokenValue.EQUAL):
            equals = self.previous()
            value = self.assignment()  # allow chaining (a = b = c)

            if isinstance(expr, Variable):
                return Assign(expr.name, value)

            self.error(equals, "Invalid assignment target.")

        return expr
    
    def equality(self):
        """
        Parse equality expressions (==, !=).

        Returns:
            Expression: An equality expression node or lower-precedence node.
        """
        left = self.comparison()

        while self.match(TokenValue.EQUAL_EQUAL, TokenValue.BANG_EQUAL):
            operator = self.previous()
            right = self.comparison()
            left = Binary(left, operator, right)
        
        return left
    
    def comparison(self):
        """
        Parse comparison expressions (<, <=, >, >=).

        Returns:
            Expression: A comparison expression node or lower-precedence node.
        """
        left = self.term()

        while self.match(TokenValue.GREATER, TokenValue.GREATER_EQUAL,
                         TokenValue.LESS, TokenValue.LESS_EQUAL):
            operator = self.previous()
            right = self.term()
            left = Binary(left, operator, right)

        return left

    def term(self):
        """
        Parse addition and subtraction expressions (+, -).

        Returns:
            Expression: A term expression node or lower-precedence node.
        """
        left = self.factor()

        while self.match(TokenValue.MINUS, TokenValue.PLUS):
            operator = self.previous()
            right = self.factor()
            left = Binary(left, operator, right)

        return left

    def factor(self):
        """
        Parse multiplication and division expressions (*, /).

        Returns:
            Expression: A factor expression node or lower-precedence node.
        """
        left = self.unary()

        while self.match(TokenValue.SLASH, TokenValue.STAR):
            operator = self.previous()
            right = self.unary()
            left = Binary(left, operator, right)

        return left

    def unary(self):
        """
        Parse unary expressions (!, -).

        Returns:
            Expression: A unary node or primary expression node.
        """
        if self.match(TokenValue.BANG, TokenValue.MINUS):
            operator = self.previous()
            right = self.unary()
            return Unary(operator, right)

        return self.primary()

    def primary(self):
        """
        Parse primary expressions (literals, parenthesized expressions).

        Returns:
            Expression: A literal, grouped expression, or raises a parse error.
        """
        if self.match(TokenValue.FALSE):
            return Literal(False)
        if self.match(TokenValue.TRUE):
            return Literal(True)
        if self.match(TokenValue.NULL):
            return Literal(None)
        if self.match(TokenValue.NUMBER, TokenValue.STRING):
            return Literal(self.previous().literal)
        if self.match(TokenValue.IDENTIFIER):
            return self.finish_call(Variable(self.previous().lexeme))
        if self.match(TokenValue.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenValue.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)
        self.error(self.peek(), "Expect expression.")
    

    def finish_call(self, callee):
        while True:
            if self.match(TokenValue.LEFT_PAREN):
                arguments = []
                if not self.check(TokenValue.RIGHT_PAREN):
                    while True:
                        arguments.append(self.expression())
                        if not self.match(TokenValue.COMMA):
                            break
                paren = self.consume(TokenValue.RIGHT_PAREN, "Expect ')' after arguments.")
                callee = Call(callee, paren, arguments)
            else:
                break
        return callee


    def synchronize(self):
        """
        Error recovery method.
        Advances tokens until a safe synchronization point is found.
        """
        self.advance()
        while not self.is_at_end():
            if self.previous().type == TokenValue.SEMICOLON:
                return
            
            if self.match(TokenValue.SLOTH,
                          TokenValue.FUN,
                          TokenValue.NEW,
                          TokenValue.FOR,
                          TokenValue.IF,
                          TokenValue.WHILE,
                          TokenValue.PRINT,
                          TokenValue.GIVE):
                return
            self.advance()
        return
        
    def consume(self, token_type, message):
        """
        Ensure the current token matches the expected type.

        Args:
            token_type (TokenValue): The expected token type.
            message (str): The error message if expectation fails.

        Returns:
            Token: The consumed token.

        Raises:
            ParseError: If the expected token is not found.
        """
        if self.check(token_type):
            return self.advance()
        raise self.error(self.peek(), message)

    def match(self, *types):
        """
        Check if the current token matches any of the given types.

        Args:
            *types (TokenValue): Token types to check.

        Returns:
            bool: True if a match is found and token is consumed, else False.
        """
        for t in types:
            if self.check(t):
                self.advance()
                return True
        return False

    def check(self, token_type):
        """
        Check if the current token is of the given type.

        Args:
            token_type (TokenValue): The type to check against.

        Returns:
            bool: True if current token matches, False otherwise.
        """
        return self.peek().type == token_type

    def advance(self):
        """
        Consume the current token and move to the next one.

        Returns:
            Token: The previous token.
        """
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self):
        """
        Check if the parser has reached the end of the token list.

        Returns:
            bool: True if the current token is EOF, False otherwise.
        """
        if self.peek().type == TokenValue.EOF:
            return True
        else:
            return False

    def peek(self):
        """
        Get the current token without consuming it.

        Returns:
            Token: The current token.
        """
        if self.tokens[-1].line >= len(self.tokens):
            return Token(TokenValue.EOF, "", None, self.current)
        return self.tokens[self.current]

    def previous(self):
        """
        Get the most recently consumed token.

        Returns:
            Token: The previous token.
        """
        return self.tokens[self.current - 1]

    def error(self, token, message):
        """
        Report a parsing error.

        Args:
            token (Token): The token that caused the error.
            message (str): The error message.

        Raises:
            ParseError: Always raises to signal parse failure.
        """
        ErrorHandler.error(token, message)
        raise ParseError(token, message)

    def __str__(self):
        """
        Return a string representation of the parser state.

        Returns:
            str: A debug string showing current index and AST.
        """
        return f"Parser(current={self.current}, ast={self.ast})"

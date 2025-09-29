from error_handler import *
from custom_token import *
from expression import *


class Parser():
    """
    Map tokens to terminals
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0
        self.parse()


    def parse(self):
        """
        Start parsing the tokens
        """
        try:
            self.ast = self.expression()
            return self.ast
        except ParseError:
            self.synchronize()
            return None


    def expression(self):
        return self.equality()
    
    
    def equality(self):
        left = self.comparison()

        while self.match(TokenValue.EQUAL_EQUAL, TokenValue.BANG_EQUAL):
            operator = self.previous()
            right = self.comparison()
            left = Binary(left, operator, right)
        
        return left
    

    def comparison(self):
        left = self.term()

        while self.match(TokenValue.GREATER, TokenValue.GREATER_EQUAL,
                        TokenValue.LESS, TokenValue.LESS_EQUAL):
            operator = self.previous()
            right = self.term()
            left = Binary(left, operator, right)

        return left


    def term(self):
        left = self.factor()

        while self.match(TokenValue.MINUS, TokenValue.PLUS):
            operator = self.previous()
            right = self.factor()
            left = Binary(left, operator, right)

        return left


    def factor(self):
        left = self.unary()

        while self.match(TokenValue.SLASH, TokenValue.STAR):
            operator = self.previous()
            right = self.unary()
            left = Binary(left, operator, right)

        return left


    def unary(self):
        if self.match(TokenValue.BANG, TokenValue.MINUS):
            operator = self.previous()
            right = self.unary()
            return Unary(operator, right)

        return self.primary()


    def primary(self):
        if self.match(TokenValue.FALSE):
            return Literal(False)
        if self.match(TokenValue.TRUE):
            return Literal(True)
        if self.match(TokenValue.NULL):
            return Literal(None)

        if self.match(TokenValue.NUMBER, TokenValue.STRING):
            return Literal(self.previous().literal)

        if self.match(TokenValue.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenValue.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)

        # If nothing matched, it's a parse error
        self.error(self.peek(), "Expect expression.")
    

    def synchronize(self):
        self.advance()
        while not self.is_at_end():
            if self.previous().type == TokenValue.SEMICOLON:
                return
            
            if self.match(TokenValue.SLOTH,
                          TokenValue.FUN,
                          TokenValue.VAR,
                          TokenValue.FOR,
                          TokenValue.IF,
                          TokenValue.WHILE,
                          TokenValue.PRINT,
                          TokenValue.GIVE):
                return
            self.advance()
            return
        

    def consume(self, token_type, message):
        if self.match(token_type):
            return self.advance()
        raise self.error(self.peek(), message)


    def match(self, *types):
        for t in types:
            if self.check(t):
                self.advance()
                return True
        return False


    def check(self, token_type):
        if self.is_at_end():
            return False
        else:
            return self.peek().type == token_type


    def advance(self):
        if not self.is_at_end():
            self.current += 1
        return self.previous()


    def is_at_end(self):
        if self.peek().type == TokenValue.EOF:
            return True
        else:
            return False


    def peek(self):
        return self.tokens[self.current]


    def previous(self):
        return self.tokens[self.current - 1]


    def error(self, token, message):
        ErrorHandler.error(token, message)
        return ParseError()


    def __str__(self):
        return f"Parser(current={self.current}, ast={self.ast})"
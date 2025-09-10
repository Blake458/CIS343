from token_values import TokenValue

class Token:

    def __init__(self, type: TokenValue, lexeme, literal, line):
        self.type = type
        self.lexeme = lexeme
        self.literal = literal
        self.line = line
    
    def __str__(self):
        return f"{self.type} | {self.lexeme} | {self.literal}"
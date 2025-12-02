from token_values import TokenValue

class Token:

    def __init__(self, token_type: TokenValue, lexeme, literal, line):
        self.type = token_type
        self.lexeme = lexeme
        self.literal = literal
        self.line = line
    
    def __str__(self):
        return f"{self.type} | {self.lexeme} | {self.literal}"
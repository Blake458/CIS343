import sys
from custom_token import *

class ErrorHandler(Exception):
    error_detected = False

    @staticmethod
    def error(error, message):
        if isinstance(error, Token):
            if(error.type == TokenValue.EOF):
                ErrorHandler.report(error.line, " at end", message)
            else:
                ErrorHandler.report(error.line, f" at '{error.lexeme}'", message)
        else:
            ErrorHandler.report(error, "", message)

    @staticmethod
    def report(line, where, message):
        print(f"LINE: {line}\nERROR: {where}: {message}")
        ErrorHandler.error_detected = True
        
class ParseError(RuntimeError):
    pass

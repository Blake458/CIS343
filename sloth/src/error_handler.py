import sys
from custom_token import Token, TokenValue

class ErrorHandler:
    error_detected = False  # class-level flag

    @staticmethod
    def error(error, message):
        """Handle both token-based and line-based errors."""
        if isinstance(error, Token):
            if error.type == TokenValue.EOF:
                ErrorHandler.report(error.line, " at end", message)
            else:
                ErrorHandler.report(error.line, f" at '{error.lexeme}'", message)
        else:
            # fallback: just line number
            ErrorHandler.report(error, "", message)

    @staticmethod
    def report(line, where, message):
        print(f"[line {line}] Error{where}: {message}", file=sys.stderr)
        ErrorHandler.error_detected = True

    @staticmethod
    def reset():
        """Reset error flag between runs (useful for REPL mode)."""
        ErrorHandler.error_detected = False


class ParseError(RuntimeError):
    """Raised when a parsing error occurs."""

    def __init__(self, token: Token, message: str):
        super().__init__(message)
        print(f"[Parse Error at '{token.lexeme}' (line {token.line})] {message}", file=sys.stderr)

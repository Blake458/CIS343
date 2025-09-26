"""
AST Printer that produces parenthesized expressions like:

    (* (- 123) (group 45.67))

This file assumes `expression.py` (generated) is available in the same directory.
"""

from expression import Binary, Grouping, Literal, Unary, Visitor

class AstPrinter(Visitor):
    """
    Walks the AST and returns a string representation with parentheses.
    """

    def parenthesize(self, name, *parts):
        """Helper to build parenthesized lists. parts are strings."""
        if not parts:
            return f"({name})"
        return "(" + " ".join([name] + list(parts)) + ")"

    def stringify_token(self, token):
        """
        Tries to get a meaningful string from a token-like object.
        If token has attribute 'lexeme', uses that. Otherwise fallback to str(token).
        """
        if token is None:
            return "nil"
        if hasattr(token, "lexeme"):
            return str(token.lexeme)
        # maybe the token is just a string/number
        return str(token)

    def visit_Binary(self, node: Binary):
        left = node.left.accept(self) if hasattr(node.left, "accept") else str(node.left)
        right = node.right.accept(self) if hasattr(node.right, "accept") else str(node.right)
        op = self.stringify_token(node.operator)
        return self.parenthesize(op, left, right)

    def visit_Grouping(self, node: Grouping):
        inner = node.expression.accept(self) if hasattr(node.expression, "accept") else str(node.expression)
        return self.parenthesize("group", inner)

    def visit_Literal(self, node: Literal):
        # Make sure strings are printed as-is (no quotes) to match your example
        val = node.value
        if val is None:
            return "nil"
        return str(val)

    def visit_Unary(self, node: Unary):
        right = node.right.accept(self) if hasattr(node.right, "accept") else str(node.right)
        op = self.stringify_token(node.operator)
        return self.parenthesize(op, right)


if __name__ == "__main__":
    # We build this AST:
    # expression = Binary(
    #   Unary(Token(TokenType.MINUS, "-", None, 1), Literal(123)),
    #   Token(TokenType.STAR, "*", None, 1),
    #   Grouping(Literal(45.67)),
    # )
    #
    # The printer should output: (* (- 123) (group 45.67))

    # Because we don't have a Token class here, create a tiny stand-in:
    class Token:
        def __init__(self, lexeme):
            self.lexeme = lexeme
        def __repr__(self):
            return f"Token({self.lexeme})"

    # Build nodes using the generated classes
    left_unary = Unary(Token("-"), Literal(123))
    right_group = Grouping(Literal(45.67))
    expr = Binary(left_unary, Token("*"), right_group)

    printer = AstPrinter()
    out = expr.accept(printer)
    print(out)  # expected: (* (- 123) (group 45.67))

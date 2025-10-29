"""
AST Printer that produces parenthesized expressions like:

    (* (- 123) (group 45.67))

This file assumes `expression.py` (generated) is available in the same directory.
"""

from expression import *
from visitor import Visitor

class AstPrinter(Visitor):
    """
    Walks an Abstract Syntax Tree (AST) and returns a string representation
    with parenthesized prefix notation, e.g., `(+ 1 2)`.
    """

    def parenthesize(self, name, *parts):
        """
        Build a parenthesized string representation.

        Args:
            name (str): The operator or grouping name to use as the root.
            *parts (str): Zero or more string representations of child expressions.

        Returns:
            str: A parenthesized string like "(name part1 part2 ...)".
        """
        if not parts:
            return f"({name})"
        return "(" + " ".join([name] + list(parts)) + ")"

    def stringify_token(self, token):
        """
        Convert a token-like object to a meaningful string.

        Args:
            token (Token | Any): The token or object to stringify.

        Returns:
            str: The token's lexeme if available, "nil" if None, or str(token) otherwise.
        """
        if token is None:
            return "nil"
        if hasattr(token, "lexeme"):
            return str(token.lexeme)
        return str(token)

    def visit_Binary(self, node: Binary):
        """
        Visit a Binary expression node and return its parenthesized string.

        Args:
            node (Binary): The binary expression node with 'left', 'operator', 'right'.

        Returns:
            str: A string like "(operator left right)" representing the node.
        """
        left = node.left.accept(self) if hasattr(node.left, "accept") else str(node.left)
        right = node.right.accept(self) if hasattr(node.right, "accept") else str(node.right)
        op = self.stringify_token(node.operator)
        return self.parenthesize(op, left, right)

    def visit_Grouping(self, node: Grouping):
        """
        Visit a Grouping node and return its parenthesized string.

        Args:
            node (Grouping): A grouping node with 'expression'.

        Returns:
            str: A string like "(group inner)" representing the grouped expression.
        """
        inner = node.expression.accept(self) if hasattr(node.expression, "accept") else str(node.expression)
        return self.parenthesize("group", inner)

    def visit_Literal(self, node: Literal):
        """
        Visit a Literal node and return its string representation.

        Args:
            node (Literal): A literal node with 'value'.

        Returns:
            str: The literal value as a string, or "nil" if None.
        """
        val = node.value
        if val is None:
            return "nil"
        return str(val)

    def visit_Unary(self, node: Unary):
        """
        Visit a Unary expression node and return its parenthesized string.

        Args:
            node (Unary): A unary expression node with 'operator' and 'right'.

        Returns:
            str: A string like "(operator right)" representing the node.
        """
        right = node.right.accept(self) if hasattr(node.right, "accept") else str(node.right)
        op = self.stringify_token(node.operator)
        return self.parenthesize(op, right)

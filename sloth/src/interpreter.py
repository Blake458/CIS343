"""
Interpreter for Sloth
by Blake Collins
"""
from visitor import *
from environment import Environment

class Interpreter(Visitor):
    def __init__(self):
        self.environment = Environment()  # store all variables here

    # ---- Expression Visitors ----
    def visit_Grouping(self, expression):
        return expression.expression.accept(self)

    def visit_Literal(self, expression):
        return expression.value

    def visit_Unary(self, expression):
        right = expression.right.accept(self)
        op = expression.operator.lexeme

        if op == "-":
            if not isinstance(right, (int, float)):
                raise RuntimeError("Operand must be a number for unary '-'")
            return -right
        elif op == "!":
            return not right
        else:
            raise RuntimeError(f"Unknown unary operator {op}")


    def visit_Binary(self, expression):
        left = expression.left.accept(self)
        right = expression.right.accept(self)
        op = expression.operator.lexeme

        if op == "+":
            if isinstance(left, str) or isinstance(right, str):
                # allow string concatenation
                return str(left) + str(right)
            if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
                raise RuntimeError("Operands must be numbers or strings for '+'")
            return left + right

        elif op == "-":
            self._check_number_operands(op, left, right)
            return left - right
        elif op == "*":
            self._check_number_operands(op, left, right)
            return left * right
        elif op == "/":
            self._check_number_operands(op, left, right)
            if right == 0:
                raise RuntimeError("Division by zero")
            return left / right
        elif op == "==":
            return left == right
        elif op == "!=":
            return left != right
        elif op in [">", ">=", "<", "<="]:
            self._check_number_operands(op, left, right)
            if op == ">": return left > right
            if op == ">=": return left >= right
            if op == "<": return left < right
            if op == "<=": return left <= right
        else:
            raise RuntimeError(f"Unknown binary operator {op}")


    def _check_number_operands(self, operator, left, right):
        if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
            raise RuntimeError(f"Operands must be numbers for '{operator}'")


    def visit_Variable(self, expression):
        # Expression: just retrieve the variable value
        return self.environment.get(expression.name)


    def visit_Assign(self, expression):
        # Expression: variable = value
        value = expression.value.accept(self)
        self.environment.assign(expression.name, value)
        return value  # allow chained assignments
    

    def visit_AssignStmt(self, stmt):
        value = stmt.value.accept(self)
        self.environment.assign(stmt.name, value)
        # Don't return anything


    def visit_VarStmt(self, stmt):
        # Statement: var a = 5;
        value = None
        if stmt.initializer is not None:
            value = stmt.initializer.accept(self)
        self.environment.define(stmt.name, value)
        return None

    def visit_PrintStmt(self, stmt):
        value = stmt.expression.accept(self)
        
        # Convert Sloth booleans/null to uppercase strings
        if value is True:
            print("TRUE")
        elif value is False:
            print("FALSE")
        elif value is None:
            print("NULL")
        else:
            print(value)


    def visit_ExpressionStmt(self, stmt):
        stmt.expression.accept(self)

    def visit_Block(self, stmt):
        """
        Execute a block statement with its own scope.
        """
        # Create a new environment for the block
        previous = self.environment
        self.environment = Environment(previous)
        try:
            for statement in stmt.statements:
                statement.accept(self)
        finally:
            # Restore the previous environment
            self.environment = previous

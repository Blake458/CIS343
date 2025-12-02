"""
Interpreter for Sloth Programming Language
by Blake Collins

This module implements the interpreter that executes Sloth AST nodes.
It handles variable scoping, function calls, class instantiation, and inheritance.
"""

# Custom packages
from environment import Environment
from sloth_function import *
from sloth_class import SlothClass, SlothInstance
from visitor import Visitor

class Interpreter(Visitor):
    """Main interpreter class that executes Sloth AST nodes using the visitor pattern."""
    
    def __init__(self):
        """Initialize the interpreter with global environment and built-in functions."""
        self.globals = Environment()
        self.environment = self.globals
        self.locals = {}  # Maps expressions to their resolved scope distances
        
        # Define built-in functions
        self.globals.define("clock", ClockFunction())
        self.globals.define("delay", DelayFunction())
        
        self.debug = False  # Set to True for debug output

    def _get_name(self, name_token_or_str):
        """Extract string name from either a Token object or string."""
        return name_token_or_str.lexeme if hasattr(name_token_or_str, 'lexeme') else name_token_or_str

    def debug_print(self, message):
        """Print debug message only if debug mode is enabled."""
        if self.debug:
            print(message)

    # ============================================================================
    # CORE INTERPRETER METHODS
    # ============================================================================

    def resolve(self, expr, dist):
        """Store the resolved distance for a variable expression."""
        self.locals[expr] = dist

    def interpret(self, statements):
        """Execute a list of statements."""
        try:
            for statement in statements:
                statement.accept(self)
        except RuntimeError as error:
            # Proper error handling would go here
            raise error

    def evaluate(self, expr):
        """Evaluate an expression and return its value."""
        return expr.accept(self)

    def execute_block(self, statements, environment):
        """Execute a block of statements in a new environment."""
        previous = self.environment
        try:
            self.environment = environment
            # Handle both Block objects and raw statement lists
            stmts_list = statements.statements if hasattr(statements, 'statements') else statements
            for stmt in stmts_list:
                stmt.accept(self)
        finally:
            self.environment = previous

    def lookup_variable(self, name_token_or_str, expr):
        """Look up a variable in the appropriate scope based on resolver distance."""
        name = self._get_name(name_token_or_str)
        distance = self.locals.get(expr)
        
        if distance is not None:
            # Variable was resolved to a specific scope distance
            self.debug_print(f"[Debug] Resolving '{name}' at distance {distance}")
            return self.environment.get_at(distance, name)
        else:
            # Variable is global
            return self.globals.get(name)

    # ============================================================================
    # EXPRESSION VISITORS
    # ============================================================================

    def visit_Variable(self, expr):
        """Handle variable access."""
        return self.lookup_variable(expr.name, expr)

    def visit_Assign(self, stmt):
        """Handle variable assignment."""
        value = self.evaluate(stmt.value)
        name = self._get_name(stmt.name)
        distance = self.locals.get(stmt)
        
        if distance is not None:
            self.environment.assign_at(distance, name, value)
        else:
            self.globals.assign(name, value)
        return value

    def visit_Literal(self, expr):
        """Handle literal values (numbers, strings, booleans, null)."""
        return expr.value
    
    def visit_Grouping(self, expr):
        """Handle parenthesized expressions."""
        return self.evaluate(expr.expression)

    def visit_Unary(self, expr):
        """Handle unary operators (-, !)."""
        right = self.evaluate(expr.right)
        op = expr.operator.lexeme
        
        if op == "-":
            if not isinstance(right, (int, float)): 
                raise RuntimeError("Operand must be a number for unary '-'")
            return -right
        elif op == "!": 
            return not self._is_truthy(right)
        else:
            raise RuntimeError(f"Unknown unary operator {op}")

    def visit_Binary(self, expr):
        """Handle binary operators (+, -, *, /, ==, !=, <, <=, >, >=)."""
        l, r = self.evaluate(expr.left), self.evaluate(expr.right)
        op = expr.operator.lexeme
        
        # Arithmetic and string concatenation
        if op == "+":
            if isinstance(l, str) or isinstance(r, str): 
                return str(l) + str(r)
            if isinstance(l, (int, float)) and isinstance(r, (int, float)): 
                return l + r
            raise RuntimeError("Operands must be two numbers or two strings.")
        
        # Arithmetic operations
        elif op == "-": 
            self._check_number_operands(op, l, r)
            return l - r
        elif op == "*": 
            self._check_number_operands(op, l, r)
            return l * r
        elif op == "/":
            self._check_number_operands(op, l, r)
            if r == 0: raise RuntimeError("Division by zero")
            return l / r
        
        # Equality operations
        elif op == "==": return l == r
        elif op == "!=": return l != r
        
        # Comparison operations
        elif op in (">", ">=", "<", "<="):
            self._check_number_operands(op, l, r)
            if op == ">": return l > r
            elif op == ">=": return l >= r
            elif op == "<": return l < r
            elif op == "<=": return l <= r
        
        else:
            raise RuntimeError(f"Unknown binary operator {op}")

    def visit_Call(self, expr):
        """Handle function and class constructor calls."""
        callee = self.evaluate(expr.callee)
        arguments = [self.evaluate(arg) for arg in expr.arguments]

        if not isinstance(callee, SlothCallable):
            raise RuntimeError("Can only call functions and slothes.")

        # Check argument count
        if len(arguments) != callee.arity():
            raise RuntimeError(f"Expected {callee.arity()} arguments but got {len(arguments)}.")
        
        # Handle class instantiation
        if isinstance(callee, SlothClass):
            instance = SlothInstance(callee)
            initializer = callee.find_method("init")
            if initializer:
                initializer.bind(instance).call(self, arguments)
            return instance
        
        # Handle function calls
        return callee.call(self, arguments)

    # ============================================================================
    # OBJECT-ORIENTED FEATURES
    # ============================================================================

    def visit_Get(self, expr):
        """Handle property access (obj.property)."""
        obj = self.evaluate(expr.object)
        if isinstance(obj, SlothInstance):
            return obj.get(self._get_name(expr.name))
        raise RuntimeError("Only instances have properties.")

    def visit_Set(self, expr):
        """Handle property assignment (obj.property = value)."""
        obj = self.evaluate(expr.object)
        if not isinstance(obj, SlothInstance):
            raise RuntimeError("Only instances have fields.")
        
        value = self.evaluate(expr.value)
        obj.set(self._get_name(expr.name), value)
        return value

    def visit_This(self, expr):
        """Handle 'this' keyword in methods."""
        return self.lookup_variable("this", expr)

    def visit_SuperSloth(self, expr):
        """Handle 'super' keyword for calling parent methods."""
        distance = self.locals.get(expr)
        supersloth = self.environment.get_at(distance, "supersloth")
        # 'this' is always one level closer than 'super'
        instance = self.environment.get_at(distance - 1, "this")
        method_name = self._get_name(expr.method)
        method = supersloth.find_method(method_name)
        
        if method is None:
            raise RuntimeError(f"Undefined property '{method_name}' on supersloth.")

        return method.bind(instance)

    # ============================================================================
    # STATEMENT VISITORS
    # ============================================================================

    def visit_Block(self, stmt):
        """Handle block statements with new scope."""
        self.execute_block(stmt.statements, Environment(self.environment))

    def visit_VarStmt(self, stmt):
        """Handle variable declarations."""
        val = self.evaluate(stmt.initializer) if stmt.initializer else None
        self.environment.define(self._get_name(stmt.name), val)

    def visit_Function(self, stmt):
        """Handle function declarations."""
        func = SlothFunction(stmt, self.environment, is_initializer=(self._get_name(stmt.name) == "init"))
        self.environment.define(self._get_name(stmt.name), func)

    def visit_Sloth(self, stmt):
        """Handle class declarations."""
        sloth_name = self._get_name(stmt.name)
        supersloth = None
        
        # Handle inheritance
        if stmt.supersloth:
            supersloth = self.evaluate(stmt.supersloth)
            if not isinstance(supersloth, SlothClass):
                raise RuntimeError("Supersloth must be a sloth.")

        # Define the class name first to allow self-reference
        self.environment.define(sloth_name, None)

        # Create new environment for super if needed
        if stmt.supersloth:
            self.environment = Environment(self.environment)
            self.environment.define("supersloth", supersloth)

        # Process all methods
        methods = {}
        for method_stmt in stmt.methods:
            method_name = self._get_name(method_stmt.name)
            is_init = (method_name == "init")
            function = SlothFunction(method_stmt, self.environment, is_initializer=is_init)
            methods[method_name] = function
        
        # Create the class
        klass = SlothClass(sloth_name, supersloth, methods)

        # Restore previous environment
        if supersloth:
            self.environment = self.environment.enclosing
        
        self.environment.assign(sloth_name, klass)

    def visit_ReturnStmt(self, stmt):
        """Handle return statements."""
        val = self.evaluate(stmt.value) if stmt.value else None
        raise ReturnException(val)

    def visit_ExpressionStmt(self, stmt): 
        """Handle expression statements."""
        self.evaluate(stmt.expression)

    def visit_PrintStmt(self, stmt):
        """Handle print statements with proper formatting."""
        value = self.evaluate(stmt.expression)
        if value is True: 
            print("TRUE")
        elif value is False: 
            print("FALSE")
        elif value is None: 
            print("NULL")
        else: 
            print(value)

    # ============================================================================
    # CONTROL FLOW
    # ============================================================================

    def visit_IfStmt(self, stmt):
        """Handle if-else statements."""
        if self._is_truthy(self.evaluate(stmt.condition)): 
            stmt.then_branch.accept(self)
        elif stmt.else_branch: 
            stmt.else_branch.accept(self)

    def visit_WhileStmt(self, stmt):
        """Handle while loops."""
        while self._is_truthy(self.evaluate(stmt.condition)): 
            stmt.body.accept(self)

    def visit_ForStmt(self, stmt):
        """Handle for loops."""
        # Execute initializer if present
        if stmt.initializer:
            stmt.initializer.accept(self)
        
        # Loop while condition is true
        while stmt.condition is None or self._is_truthy(self.evaluate(stmt.condition)):
            # Execute body
            stmt.body.accept(self)
            
            # Execute increment if present
            if stmt.increment:
                self.evaluate(stmt.increment)

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _is_truthy(self, value):
        """Determine truthiness of a value (false and null are falsy, everything else is truthy)."""
        if value is None: return False
        if isinstance(value, bool): return value
        return True

    def _check_number_operands(self, op, l, r):
        """Ensure both operands are numbers for arithmetic operations."""
        if not isinstance(l, (int, float)) or not isinstance(r, (int, float)):
            raise RuntimeError(f"Operands must be numbers for '{op}'")


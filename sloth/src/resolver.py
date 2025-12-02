from statement import *
from expression import *
from visitor import Visitor
from sloth_class import *
from sloth_function import *

class Resolver(Visitor):
    def __init__(self, interpreter):
        self.interpreter = interpreter
        self.scopes = []   # stack of dicts: scope chains
        self.locals = {}  # Maps expressions to their scope distances
        self.current_function = None  # NONE, FUNCTION, METHOD, INITIALIZER
        self.current_sloth = None  # NONE, SLOTH, SUBSLOTH
        self.debug = False  # Set to True to enable debug output

    def debug_print(self, message):
        """Print debug message only if debug is enabled."""
        if self.debug:
            print(message)

    # ---- Helpers ----
    def begin_scope(self):
        self.scopes.append({})

    def end_scope(self):
        self.scopes.pop()
    
    # CORRECTED: Consistently get string name from Token or str
    def _get_name(self, name_token_or_str):
        return name_token_or_str.lexeme if hasattr(name_token_or_str, 'lexeme') else name_token_or_str

    def declare(self, name_token_or_str):
        if not self.scopes:
            return
        scope = self.scopes[-1]
        name = self._get_name(name_token_or_str)
        if name in scope:
            self.debug_print(f"[Resolver Error] Variable '{name}' already declared in this scope.")
        scope[name] = False 

    def define(self, name_token_or_str):
        if not self.scopes:
            return
        scope = self.scopes[-1]
        name = self._get_name(name_token_or_str)
        scope[name] = True

    def resolve(self, node):
        if node is None: return
        return node.accept(self)

    def resolve_local(self, expr, name_token_or_str):
        name = self._get_name(name_token_or_str)
        for i in range(len(self.scopes) - 1, -1, -1):
            if name in self.scopes[i]:
                distance = len(self.scopes) - 1 - i
                self.locals[expr] = distance
                self.debug_print(f"[Resolver Debug] Resolving '{name}' at distance {distance}")
                self.interpreter.resolve(expr, distance)
                return
        # Not found locally, assume global (or error, depending on language rules)

    def resolve_function(self, function, function_type):
        enclosing_function = self.current_function
        self.current_function = function_type
        self.begin_scope()

        if function_type == FunctionType.METHOD or function_type == FunctionType.INITIALIZER:
            self.declare("this")
            self.define("this")

        for param in function.params:
            self.declare(param)
            self.define(param)
        
        self.resolve_all(function.body.statements)
        self.end_scope()
        self.current_function = enclosing_function

    # ---- Statement Visitors ----
    def visit_Block(self, stmt):
        self.begin_scope()
        self.resolve_all(stmt.statements)
        self.end_scope()

    def resolve_all(self, stmts):
        for stmt in stmts:
            self.resolve(stmt)

    def visit_VarStmt(self, stmt):
        self.declare(stmt.name)
        if stmt.initializer is not None:
            self.resolve(stmt.initializer)
        self.define(stmt.name)

    def visit_Assign(self, expr):
        self.resolve(expr.value)
        self.resolve_local(expr, expr.name)

    def visit_Function(self, stmt):
        self.declare(stmt.name)
        self.define(stmt.name)
        self.resolve_function(stmt, FunctionType.FUNCTION)

    def visit_ExpressionStmt(self, stmt): self.resolve(stmt.expression)
    
    def visit_PrintStmt(self, stmt): self.resolve(stmt.expression)
    
    def visit_IfStmt(self, stmt):
        self.resolve(stmt.condition)
        self.resolve(stmt.then_branch)
        if stmt.else_branch: self.resolve(stmt.else_branch)
   
    def visit_WhileStmt(self, stmt):
        self.resolve(stmt.condition)
        self.resolve(stmt.body)
    
    def visit_ForStmt(self, stmt):
        if stmt.initializer:
            self.resolve(stmt.initializer)
        if stmt.condition:
            self.resolve(stmt.condition)
        if stmt.increment:
            self.resolve(stmt.increment)
        self.resolve(stmt.body)
   
    def visit_ReturnStmt(self, stmt):
        if self.current_function == FunctionType.INITIALIZER:
            if stmt.value is not None:
                raise RuntimeError("[Resolver Error] Can't return a value from an initializer.")
        if stmt.value: 
            self.resolve(stmt.value)

    def visit_Variable(self, expr):
        name = self._get_name(expr.name)
        if self.scopes and name in self.scopes[-1] and self.scopes[-1].get(name) == False:
            self.debug_print("[Resolver Error] Can't read local variable in its own initializer.")
        self.resolve_local(expr, expr.name)

    def visit_Literal(self, expr): return None
   
    def visit_Grouping(self, expr): self.resolve(expr.expression)
    
    def visit_Unary(self, expr): self.resolve(expr.right)
    
    def visit_Binary(self, expr):
        self.resolve(expr.left)
        self.resolve(expr.right)
    
    def visit_Call(self, expr):
        self.resolve(expr.callee)
        for arg in expr.arguments: self.resolve(arg)


    def visit_Sloth(self, stmt):
        enclosing_sloth = self.current_sloth
        self.current_sloth = SlothType.SLOTH

        self.declare(stmt.name)
        self.define(stmt.name)

        if stmt.supersloth:
            self.current_sloth = SlothType.SUBSLOTH
            self.resolve(stmt.supersloth)
            self.begin_scope()
            self.scopes[-1]["supersloth"] = True

        for method in stmt.methods:
            declaration = FunctionType.METHOD
            if self._get_name(method.name) == "init":
                declaration = FunctionType.INITIALIZER
            self.resolve_function(method, declaration)

        if stmt.supersloth:
            self.end_scope()

        self.current_sloth = enclosing_sloth

    def transfer_locals(self):
        for expr, distance in self.locals.items():
            self.interpreter.resolve(expr, distance)

    def visit_Get(self, expr):
        self.resolve(expr.object)
    
    def visit_Set(self, expr):
        self.resolve(expr.value)
        self.resolve(expr.object)
    
    def visit_This(self, expr):
        if self.current_sloth is None:
            self.debug_print("[Resolver Error] Can't use 'this' outside of a sloth.")
            return
        self.resolve_local(expr, "this")
    
    def visit_SuperSloth(self, expr):
        if self.current_sloth != SlothType.SUBSLOTH:
            self.debug_print("[Resolver Error] Can't use 'supersloth' outside a subsloth.")
            return
        self.resolve_local(expr, "supersloth")
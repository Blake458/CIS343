from statement import *
from expression import *
from visitor import Visitor

class Resolver(Visitor):
    def __init__(self, interpreter):
        self.interpreter = interpreter
        self.scopes = []   # stack of dicts: scope chains
        self.current_function = None

    # ---- Helpers ----
    def begin_scope(self):
        self.scopes.append({})

    def end_scope(self):
        self.scopes.pop()

    def declare(self, name):
        if not self.scopes:
            return
        scope = self.scopes[-1]
        scope[name] = False 

    def define(self, name):
        if not self.scopes:
            return
        scope = self.scopes[-1]
        scope[name] = True

    def resolve(self, node):
        if node is None: return
        return node.accept(self)

    def resolve_local(self, expr, name):
        for depth in reversed(range(len(self.scopes))):
            if name in self.scopes[depth]:
                # record distance in interpreter
                self.interpreter.resolve(expr, len(self.scopes) - 1 - depth)
                return

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
        return None

    def visit_AssignStmt(self, expr):
        self.resolve(expr.value)
        self.resolve_local(expr, expr.name)
        return None

    def visit_Function(self, stmt):
        self.declare(stmt.name)
        self.define(stmt.name)

        # resolve function body
        self.begin_scope()
        for param in stmt.params:
            self.declare(param)
            self.define(param)
        self.resolve(stmt.body)
        self.end_scope()
        return None

    def visit_ExpressionStmt(self, stmt):
        self.resolve(stmt.expression)

    def visit_PrintStmt(self, stmt):
        self.resolve(stmt.expression)

    def visit_IfStmt(self, stmt):
        self.resolve(stmt.condition)
        self.resolve(stmt.then_branch)
        if stmt.else_branch:
            self.resolve(stmt.else_branch)

    def visit_WhileStmt(self, stmt):
        self.resolve(stmt.condition)
        self.resolve(stmt.body)

    def visit_ForStmt(self, stmt):
        self.begin_scope()
        if stmt.initializer:
            self.resolve(stmt.initializer)
        if stmt.condition:
            self.resolve(stmt.condition)
        if stmt.increment:
            self.resolve(stmt.increment)
        self.resolve(stmt.body)
        self.end_scope()

    def visit_ReturnStmt(self, stmt):
        if stmt.value:
            self.resolve(stmt.value)
        return None

    # ---- Expression Visitors ----
    def visit_Variable(self, expr):
        if self.scopes:
            if self.scopes[-1].get(expr.name) == False:
                print("[Resolver Error] Can't read local variable in its own initializer.")
        self.resolve_local(expr, expr.name)
        return None

    def visit_Literal(self, expr):
        return None

    def visit_Grouping(self, expr):
        self.resolve(expr.expression)

    def visit_Unary(self, expr):
        self.resolve(expr.right)

    def visit_Binary(self, expr):
        self.resolve(expr.left)
        self.resolve(expr.right)

    def visit_Call(self, expr):
        self.resolve(expr.callee)
        for arg in expr.arguments:
            self.resolve(arg)

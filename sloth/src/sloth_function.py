import time
from environment import Environment
import abc


class ReturnException(Exception):
    def __init__(self, value):
        self.value = value


class SlothCallable:
    def arity(self):
        return 0
    
    def call(self, interpreter, arguments):
        raise NotImplementedError
    

class SlothFunction(SlothCallable):
    def __init__(self, declaration, closure):
        self.declaration = declaration
        self.closure = closure

    def arity(self):
        return len(self.declaration.params)

    def call(self, interpreter, arguments):
        # new environment chained to the closure
        environment = Environment(self.closure)

        for param, arg in zip(self.declaration.params, arguments):
            environment.define(param.lexeme, arg)

        try:
            interpreter.execute_block(self.declaration.body.statements, environment)
        except ReturnException as ret:
            return ret.value

        return None

    def __str__(self):
        return f"<fn {self.declaration.name}>"
    

class ClockFunction(SlothCallable):
    def arity(self):
        return 0

    def call(self, interpreter, arguments):
        return time.time()

    def __str__(self):
        return "<native fn clock>"
    

class DelayFunction(SlothCallable):
    def arity(self):
        return 1

    def call(self, interpreter, arguments):
        seconds = arguments[0]
        if not isinstance(seconds, (int, float)):
            raise RuntimeError("Srgument must be of type float or int")
        time.sleep(seconds)
        return None

    def __str__(self):
        return "<native fn delay>"
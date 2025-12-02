import time
from environment import Environment
import abc


class SlothCallable:
    def arity(self):
        return 0
    
    def call(self, interpreter, arguments, instance=None):
        raise NotImplementedError
    

class SlothFunction(SlothCallable):
    def __init__(self, declaration, closure, is_initializer=False):
        self.declaration = declaration
        self.closure = closure
        self.is_initializer = is_initializer
        self.debug = False

    def debug_print(self, message):
        if self.debug:
            print(f"[Debug][SlothFunction] {message}")

    def arity(self):
        return len(self.declaration.params)

    def call(self, interpreter, arguments, instance=None):
        # The environment's parent is the function's original closure
        environment = Environment(self.closure)

        # If it's a bound method, define 'this'
        if instance:
            self.debug_print(f"Defining 'this' for instance: {instance} in call environment")
            environment.define("this", instance)

        # Populate parameters into the same environment
        for i, param in enumerate(self.declaration.params):
            environment.define(param.lexeme, arguments[i])
        
        try:
            interpreter.execute_block(self.declaration.body, environment)
        except ReturnException as ret:
            if self.is_initializer:
                return instance # In an initializer, return the instance ('this')
            return ret.value
        
        if self.is_initializer:
            return instance # Always return 'this' from init
        
        return None
    
    def bind(self, instance):
        self.debug_print(f"Binding 'this' to instance: {instance}")
        
        class BoundSlothFunction(SlothCallable):
            def __init__(self, func, instance):
                self.func = func
                self.instance = instance

            def arity(self):
                return self.func.arity()

            def call(self, interpreter, arguments, _=None): # Ignore instance passed here
                return self.func.call(interpreter, arguments, self.instance)

            def __str__(self):
                return self.func.__str__()

        return BoundSlothFunction(self, instance)

    def __str__(self):
        return f"<fn {self.declaration.name}>"
    

class ClockFunction(SlothCallable):
    def arity(self):
        return 0

    def call(self, interpreter, arguments, instance=None):
        return time.time()

    def __str__(self):
        return "<native fn clock>"
    

class DelayFunction(SlothCallable):
    def arity(self):
        return 1

    def call(self, interpreter, arguments, instance=None):
        seconds = arguments[0]
        if not isinstance(seconds, (int, float)):
            raise RuntimeError("Argument must be of type float or int")
        time.sleep(seconds)
        return None

    def __str__(self):
        return "<native fn delay>"


class FunctionType:
    NONE = "NONE"
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    INITIALIZER = "INITIALIZER"


class ReturnException(Exception):
    def __init__(self, value):
        super().__init__()
        self.value = value
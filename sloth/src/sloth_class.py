from sloth_function import SlothCallable


class SlothClass(SlothCallable):
    def __init__(self, name, supersloth, methods):
        self.name = name
        self.supersloth = supersloth
        self.methods = methods

    def call(self, interpreter, arguments):
        # Create a new instance
        instance = SlothInstance(self)
        # Find initializer (constructor) if exists
        initializer = self.find_method("init")
        if initializer:
            initializer.bind(instance).call(interpreter, arguments)
        return instance

    def arity(self):
        initializer = self.find_method("init")
        return initializer.arity() if initializer else 0

    def find_method(self, name):
        # If name is a token, get the lexeme
        if name in self.methods:
            return self.methods[name]
        if self.supersloth is not None:
            return self.supersloth.find_method(name)
        return None


    
    def instantiate(self):
        return SlothInstance(self)
    
    def __str__(self):
        return self.name
    

class SlothInstance(SlothCallable):
    def __init__(self, sloth_class):
        self.sloth_class = sloth_class
        self.fields = {}

    def get(self, name):
        if name in self.fields:
            return self.fields[name]
        
        method = self.sloth_class.find_method(name)
        if method:
            return method.bind(self)
        raise RuntimeError("Undefined property '" + name + "'.")

    def set(self, name, value):
        self.fields[name.lexeme if hasattr(name, "lexeme") else name] = value

    def __str__(self):
        return f"<{self.sloth_class.name} instance>"

class SlothType:
    NONE = "NONE"
    SLOTH = "SLOTH"
    SUBSLOTH = "SUBSLOTH"

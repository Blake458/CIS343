class Environment:
    def __init__(self, enclosing=None):
        self.values = {}
        self.enclosing = enclosing  # parent scope (for block scoping)

    def define(self, name, value=None):
        if name in self.values:
            raise RuntimeError(f"Variable '{name}' already declared in this scope.")
        self.values[name] = value

    def get(self, name):
        if name in self.values:
            return self.values[name]
        if self.enclosing is not None:
            return self.enclosing.get(name)
        raise RuntimeError(f"Undefined variable '{name}'.")

    def assign(self, name, value):
        if name in self.values:
            self.values[name] = value
            return
        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return
        raise RuntimeError(f"Undefined variable '{name}'.")
    
    def ancestor(self, distance):
        env = self
        for _ in range(distance):
            env = env.enclosing
        return env

    def get_at(self, distance, name):
        return self.ancestor(distance).values[name]

    def assign_at(self, distance, name, value):
        self.ancestor(distance).values[name] = value
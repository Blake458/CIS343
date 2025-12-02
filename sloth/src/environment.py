class Environment:
    def __init__(self, enclosing=None):
        self.values = {}
        self.enclosing = enclosing  # parent scope (for block scoping)
        self.depth = 0 if enclosing is None else enclosing.depth + 1
        self.debug = False  # Set to True to enable debug output

    def debug_print(self, message):
        if self.debug:
            print(f"[Debug][Env Depth {self.depth}] {message}")

    def define(self, name, value=None):
        name_str = name.lexeme if hasattr(name, 'lexeme') else name
        if name_str in self.values:
            # This check is good but might be too strict if you allow shadowing intentionally.
            # For now, let's keep it.
            pass
        self.debug_print(f"Defining variable '{name_str}' with value: {value}")
        self.values[name_str] = value

    def get(self, name):
        self.debug_print(f"Getting variable '{name}'")
        if name in self.values:             # Check if variable is in current scope
            return self.values[name]        # Return its value
        if self.enclosing is not None:
            return self.enclosing.get(name) # Recur to parent scope
        raise RuntimeError(f"Undefined variable '{name}'.")

    def assign(self, name, value):
        if name in self.values:
            self.values[name] = value
            return
        if self.enclosing is not None:
            self.debug_print(f"Assigning variable '{name}' in enclosing environment")
            self.enclosing.assign(name, value)
            return
        raise RuntimeError(f"Undefined variable '{name}'.")
    
    def ancestor(self, distance):
        env = self
        for _ in range(distance):
            if env.enclosing is None:
                # Returning None is safer than raising an error here
                return None
            env = env.enclosing
        return env

    def get_at(self, distance, name):
        environment = self.ancestor(distance)
        if environment and name in environment.values:
            value = environment.values.get(name)
            self.debug_print(f"Getting variable '{name}' at distance {distance} with value: {value}")
            return value
        
        raise RuntimeError(f"Undefined variable '{name}' at distance {distance}.")

    def assign_at(self, distance, name, value):
        self.debug_print(f"Assigning variable '{name}' at distance {distance} with value: {value}")
        ancestor_env = self.ancestor(distance)
        if not ancestor_env:
            raise RuntimeError(f"Invalid environment at distance {distance}")
        ancestor_env.values[name] = value
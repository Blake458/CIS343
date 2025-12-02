class Visitor:

    def visit(self, node):
        method_name = f"visit_{node.__class__.__name__}"
        visitor = getattr(self, method_name, None)

        if visitor is None:
            raise NotImplementedError(f"visit_{node.__class__.__name__} not defined")
        
        return visitor(node)
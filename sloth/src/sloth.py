# Sloth class

# Python packages
import sys

# Custom packages
from scanner import *
from parser import *
from interpreter import Interpreter
from error_handler import ErrorHandler

class Sloth:
    def __init__(self):
        self.interpreter = Interpreter()

    def run_file(self, path):
        with open(path) as file:
            self.run(file.read())

    def run_shell(self):
        try:
            print("========== SLOTH SHELL ==========")
            while True:
                line = input("> ")
                if not line.strip():
                    continue
                self.run(line)
        except KeyboardInterrupt:
            print("\n======== EXITING SLOTH SHELL ========")

    def run(self, source):
        """
        Run the scanner, parser, and interpreter
        """
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        parser = Parser(tokens)
        ast = parser.ast  # returns a list of Stmt nodes

        # Stop if syntax errors were detected
        if ErrorHandler.error_detected:
            sys.exit(65)
        else:
            # Interpret all statements
            if ast:
                for stmt in ast:
                    try:
                        result = stmt.accept(self.interpreter)
                        if result is not None and not isinstance(stmt, (AssignStmt, VarStmt)):
                            print(result)
                    except RuntimeError as e:
                        print(f"[Runtime Error] {e}")


if __name__ == "__main__":
    sloth = Sloth()
    if len(sys.argv) > 2:
        print("Usage: sloth [script]")
        sys.exit(64)
    elif len(sys.argv) == 2:
        sloth.run_file(sys.argv[1])
    else:
        sloth.run_shell()

# Sloth class

# python packages
import sys

# costom packages
from scanner import *
from parser import *
from ast_printer import *

class Sloth:

    def run_file(self, path):
        with open(path) as file:
            self.run(file.read())

    def run_shell(self):
        try:
            print("========== SLOTH SHELL ==========")
            while True:
                self.run(input("> "))
        except KeyboardInterrupt:
            print("\n======== EXITING SLOTH SHELL ========")

    def run(self, source):
        """
        Run the scanner

        input: source (file or command line text)
        output: t
        """
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        parser = Parser(tokens)
        ast = parser.parse()

        if ErrorHandler.error_detected:
            sys.exit(65)
        else:
            if ast is not None:
                printer = AstPrinter()
                print(printer.visit(ast))


if __name__ == "__main__":
    sloth = Sloth()
    if len(sys.argv) > 2:
        print("Usage: sloth [script]")
        sys.exit(64)
    elif len(sys.argv) == 2:
        sloth.run_file(sys.argv[1])
    else:
        sloth.run_shell()
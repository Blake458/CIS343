# Sloth class

# python packages
import sys

# costom packages
from error_handler import ErrorHandler
from scanner import Scanner

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
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        for token in tokens:
            print(token)


if __name__ == "__main__":
    sloth = Sloth()
    if len(sys.argv) > 2:
        print("Usage: sloth [script]")
        sys.exit(64)
    elif len(sys.argv) == 2:
        sloth.run_file(sys.argv[1])
    else:
        sloth.run_shell
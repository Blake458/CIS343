import sys

class ErrorHandler:
    error_detected = False

    @staticmethod
    def error(line, message):
        ErrorHandler.report(line, ": ", message)

    @staticmethod
    def report(line, where, message):
        print(f"LINE: {line}\nERROR: {where}: {message}")
        ErrorHandler.error_detected = True
        sys.exit()
        
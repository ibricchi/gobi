import sys

class Logger:
    @staticmethod
    def debug(message: str) -> None:
        print(f"\033[94mDEBUG: {message}\033[0m")

    @staticmethod
    def info(message: str) -> None:
        print(f"INFO: {message}")
    
    @staticmethod
    def warn(message: str) -> None:
        print(f"\033[93mWARN: {message}\033[0m", file=sys.stderr)
    
    @staticmethod
    def error(message: str) -> None:
        print(f"\033[91mERROR: {message}\033[0m", file=sys.stderr)
    
    @staticmethod
    def fatal(message: str) -> None:
        print(f"\033[91mFATAL: {message}\033[0m", file=sys.stderr)
        sys.exit(1)

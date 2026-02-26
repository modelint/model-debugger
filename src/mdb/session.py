""" session.py -- Model Debugger Session """

# System
import shlex
from pathlib import Path

class Session:
    """
    This class represents the debugger session.
    It follows the singleton pattern to ensure only one exists.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Session, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Avoid reinitialization if already initialized
        if getattr(self, "_initialized", False):
            return

        self.system_path = None

    def initialize(self, mmdb_path: Path, context_dir: Path, scenario_file: Path, verbose: bool, debug: bool):
        print("Model Debugger")
        print("Type 'help' for available commands, 'quit' to exit\n")

        while True:
            try:
                raw = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not raw:
                continue

            try:
                parts = shlex.split(raw)
            except ValueError as e:
                print(f"Parse error: {e}")
                continue

            command, *args = parts

            match command.lower():
                case "quit" | "exit":
                    break
                case "help":
                    cmd_help(args)
                case "set":
                    cmd_set(args)
                case "load":
                    cmd_load(args)
                case "list":
                    cmd_list(args)
                case _:
                    print(f"Unknown command: '{command}'. Type 'help' for available commands.")


    def cmd_help(args: list[str]) -> None:
        print("Commands:")
        print("  set <variable> <value>   - Set a variable (e.g., set syspath ~/my/path)")
        print("  load <target> [name]     - Load a target (e.g., load system, load context name)")
        print("  list <target>            - List available items (e.g., list context)")
        print("  quit / exit              - Exit the debugger")


    def cmd_set(args: list[str]) -> None:
        if len(args) < 2:
            print("Usage: set <variable> <value>")
            return
        variable, value = args[0], args[1]
        print(f"  [stub] set {variable} = {value}")


    def cmd_load(args: list[str]) -> None:
        if not args:
            print("Usage: load <target> [name]")
            return
        target = args[0]
        name = args[1] if len(args) > 1 else None
        if name:
            print(f"  [stub] load {target} '{name}'")
        else:
            print(f"  [stub] load {target}")


    def cmd_list(args: list[str]) -> None:
        if not args:
            print("Usage: list <target>")
            return
        target = args[0]
        print(f"  [stub] list {target}")
""" session.py -- Model Debugger Session """

# System
import shlex
import sys
from pathlib import Path
from typing import Optional
import logging

# MDB
from mdb.system import System
from mdb.ui_types import *

_logger = logging.getLogger(__name__)

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
        self._initialized = True

        self.system = None
        self.scenario_file = None
        self.verbose = False

    def run(self, verbose: bool,
            system_path: Optional[Path] = None,
            context_dir: Optional[Path] = None,
            scenario_file: Optional[Path] = None,
            ):
        self.system = System(system_path=system_path, context_dir=context_dir)
        self.scenario_file = scenario_file
        self.verbose = verbose

        print("Model Debugger")
        # self.system.load_models()

        # if self.context_dir:
        #     print(f"With context in: {self.context_dir}")
        # if self.scenario_file:
        #     print(f"Running scenario: {self.scenario_file}")

        print("Type 'help' for available commands, 'quit' or 'exit' to exit\n")

        while True:
            try:
                raw = input(CMD_PROMPT).strip()
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
                    self.cmd_help(args)
                case "show":
                    self.cmd_show(args)
                case "list":
                    self.cmd_list(args)
                case "set":
                    self.cmd_set(args)
                    pass
                case "load":
                    self.cmd_load(args)
                case _:
                    print(f"Unknown command: '{command}'. Type 'help' for available commands.")

    def cmd_load(self, args: list[str]) -> None:
        if len(args) < 1:
            print("Usage: set <item>")
            return

        item = args[0]
        match item:
            case 'system':
                self.system.load_models()
            case _:
                print(f"Unknown load item: {item}")
                return

    def cmd_show(self, args: list[str]) -> None:
        """
        Display requested item on console

        Args:
            args:
        """

        if len(args) < 1:
            print("Usage: set <item>")
            return

        item = args[0]
        match item:
            case 'path':
                self.system.show_path()
            case 'playgrounds':
                self.system.show_playgrounds()
            case 'active':
                if args[1] == 'playground':
                    self.system.show_active_playground()
                else:
                    print(f"Unknown active element: {args[1]}")
            case 'scenarios':
                pass
            case _:
                print(f"Unknown item: {item}")
                return

        pass
        # TODO: Have MX load the ral file and initialize the system

    def cmd_help(self, args: list[str]) -> None:
        print("Commands:")
        print("  show <item>              - Display item on console (ex: show path)")
        print("  set <variable> <value>   - Set a variable (ex: set path ~/my/path)")
        print("  load <target> [name]     - Load a target (ex: load system, load context name)")
        print("  list <target>            - List available items (ex: list context)")
        print("  quit / exit              - Exit the debugger")


    def cmd_set(self, args: list[str]) -> None:
        """
        Set the value of some variable

        Args:
            args:
        """
        if len(args) < 2:
            print("Usage: set <variable> <value>")
            return

        variable, value = args[0], args[1]
        vset = True
        match variable:
            case 'path':
                self.system.set_path(system_path=Path(value))
            case 'playground':
                self.system.set_playground(playground_name=value)
            case 'scenario':
                self.scenario_file = value
            case _:
                vset = False
                print(f"Setting {variable} not defined")

        if vset:
            print(f"{variable} = {value}")

    def cmd_list(self, args: list[str]) -> None:
        if not args:
            print("Usage: list <target>")
            return
        target = args[0]
        print(f"  [stub] list {target}")
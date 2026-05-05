""" session.py -- Model Debugger Session """

# System
import shlex
import sys
from pathlib import Path
import logging
import re
import yaml

# Model Integration
from mx.system import System

# MDB
from mdb.ui_types import *
from mdb.mdb_types import *

_logger = logging.getLogger(__name__)


def shortcut_index(s: str) -> int | None:
    """
    Convert value to an integer shortcut if it is a 1-2 char integer with no leading zeros

    Args:
        s - user string input
    Returns:
        An integer shortcut if detected, otherwise None
    """
    return int(s) if re.fullmatch(r'[1-9]\d?', s) else None


class Session:
    """
    This class represents the debugger session. It follows the singleton pattern to ensure only one exists.

    Attributes:
        system: MX system object we are debugging
        playground_name: Name of the active playground (same as file name in system playgrounds dir)
        scenario_name: Name of the active scenario (same as file name minus any extension in the
            playground scenarios dir)
        playground_scenarios: All scenario files defined for the active playground minus any file extension
        active_scenario: Name of the scenario we are currently running
        verbose: Whether verbose output is enabled
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Session, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Avoid singleton reinitialization if already initialized
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        self.system = None
        self.playground_name = None
        self.scenario_name = None
        self.playground_scenarios: list[str] = []
        self.active_scenario = None
        self.verbose = False

    def initialize(self, verbose: bool,
                   system_path: Path = None,
                   playground_name: str = None,
                   scenario_name: str = None,
                   ):
        """
        We can initialize a session without any system and then let the user initialize it interactively
        or, if a system path is provided, we can initialize it right away. The same goes for the playground and
        scenario names.

        After whatever degree of initialization is completed, we start the user command input loop

        Args:
            verbose:  Verbose mode for stdout (console) messaging/status
            system_path:  An absolute path to the system directory where the entire system is defined
            playground_name: Name of a playground corresponding ot the name of a file in the system's playground dir
            scenario_name: Name of a scenario file (yaml, for now) that the mdb loads locally, but is found in the
                system's scenarios directory
        """
        print("Initializing session from command line arguments...")
        if system_path:
            self.system = System()  # Singleton initialization
        if system_path:
            self.system.initialize(system_path=system_path, verbose=verbose)
        else:
            print("System not yet initialized. Use: set system <path> to initialize.")
        self.scenario_name = scenario_name
        self.playground_name = playground_name
        self.verbose = verbose

        # Initialize these if they were supplied on the command line
        if playground_name:
            self.set_playground(playground_name)
            if scenario_name:
                self.set_scenario(scenario_name)

        self.run()

    def run(self):
        """
        This is the user input command loop.  It just runs until the user exits.
        """

        print("\nType 'help' for available commands, 'quit' or 'exit' to exit\n")

        while True:  # Breaks out when the user enters the quit/exit command
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
                case "execute" | "x" | "exec":
                    self.execute_scenario()
                case _:
                    print(f"Unknown command: '{command}'. Type 'help' for available commands.")

    def cmd_show(self, args: list[str]) -> None:
        """
        Display requested item on console

        Args:
            args:  What to display
        """
        if len(args) < 1:
            print("Usage: set <item>")
            return

        item = args[0]
        match item:
            case 'scenario':
                print("Not implemented yet.")
            case 'path':
                self.system.show_path()
            case 'playground' | 'pg':
                print(f"Active playground: {self.system.playground}")
            case 'playgrounds' | 'pgs':
                self.show_playgrounds()
            case 'active':
                if args[1] == 'playground':
                    self.system.show_active_playground()
                else:
                    print(f"Unknown active element: {args[1]}")
            case 'scenarios':
                self.show_scenarios()
            case _:
                print(f"Unknown item: {item}")
                return

        pass
        # TODO: Have MX load the ral file and initialize the system

    def cmd_help(self, args: list[str]) -> None:
        print("Commands:")
        print("  show <item>              - Display item on console (ex: show path)")
        print("  set <variable> <value>   - Set a variable (ex: set path ~/my/path)")
        print("  execute / exec / x       - Execute the active scenario")
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
        vset = False
        match variable:
            case 'path':
                self.system.set_path(system_path=Path(value))
            case 'playground' | 'pg':
                self.set_playground(value)
            case 'scenario':
                self.set_scenario(value)
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

    def show_playgrounds(self):
        """Display all playgrounds defined in the system directory"""
        system_playgrounds = self.system.playgrounds
        if system_playgrounds is not None:
            print("Available playgrounds:")
            for n, p in enumerate(self.system.available_playgrounds):
                print(f"  [{n + 1}] - {p}")

    def set_playground(self, value: str) -> None:
        """
        Verify that the supplied value corresponds to a valid playground.

        Args:
            value: A full string name of a playground directory or shortcut 1-2 integer index
        """
        i = shortcut_index(value)  # i is between 1 and 99 or None
        if i is not None:
            if i > len(self.system.available_playgrounds):
                print(f"Undefined playground shortcut: [{value[1:]}]")
                return
            pg_name = self.system.playgrounds[i - 1]  # User counts items starting from 1
        else:
            pg_name = value
        if pg_name not in self.system.playgrounds:
            print(f"Unknown playground: {pg_name}")
            return
        print(f"Selected playground: {pg_name}")

        self.system.load_domains(playground=pg_name)
        # And find all available scenarios for that playground
        self.show_scenarios()

    def set_scenario(self, value: str):
        i = shortcut_index(value)  # i is between 1 and 99 or None
        if i is not None:
            if not self.playground_scenarios:
                print(f"Unknown scenario: {value}")
                self.show_scenarios()
                return
            if i > len(self.playground_scenarios):
                print(f"Undefined scenario shortcut: [{value[1:]}]")
                return
            scenario_name = self.playground_scenarios[i - 1]  # User counts items starting from 1
        else:
            scenario_name = value
        if scenario_name not in self.playground_scenarios:
            print(f"Unknown scenario: {scenario_name}")
            return
        print(f"Selected scenario: {scenario_name}")

        sfile = self.system.playground / 'scenarios' / (scenario_name + ".yaml")
        with open(sfile, "r") as file:
            self.active_scenario = yaml.safe_load(file)  # Load YAML content safely

    def show_scenarios(self) -> None:
        """
        Display all scenarios defined in the active playground directory
        with convenient integer shortcuts
        """
        scenario_path = self.system.playground / 'scenarios'
        scenario_paths = list(scenario_path.glob("*.yaml"))
        self.playground_scenarios = [f.stem for f in scenario_paths]
        if self.playground_scenarios:
            print("Active playground scenarios:")
            for n, p in enumerate(self.playground_scenarios):
                print(f"  [{n + 1}] - {p}")

    def execute_scenario(self) -> None:
        """
        Process each interaction of the scenario until it is complete
        """
        print(f"Running scenario: {self.active_scenario}...\n")
        System.set_announce_triggers(['external event'])
        for i in self.active_scenario['Interactions']:
            print(f"{i['description']}")

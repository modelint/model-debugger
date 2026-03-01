""" system.py -- System """

# System
from pathlib import Path
from typing import Optional
from enum import Enum

from mdb.ui_types import *

class SystemState(Enum):
    LOADED = "LOADED"
    NOT_LOADED = "NOT_LOADED"
    RUNNING = "RUNNING"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"

def validate_path(path: Path) -> bool:
    """
    Validates that a Path exists and is accessible.
    Returns True if valid, prints error to console if not and returns False
    """
    if not path.is_absolute():
        print(f"Path is not absolute: {path}")
        return False

    if not path.exists():
        print(f"Path does not exist: {path}")
        return False

    if not path.is_file() and not path.is_dir():
        print(f"Path is neither a file nor a directory: {path}")
        return False

    return True


class System:
    """
    The System being tested

    """

    def __init__(self, system_path: Optional[Path] = None, context_dir: Optional[Path] = None):

        self.path = system_path
        self.name = system_path.name if system_path else None
        self.mmdb_fname = None
        self.playground = None
        self.state = SystemState.NOT_LOADED

        if self.path:
            self.load_models()

    def load_models(self):
        """
        Tell the MX to load the system

        Returns:

        """
        print(f"Loading models for: {self.name}{STATUS}")
        self.state = SystemState.LOADED
        model_path = self.path / 'models'
        ral_files = list(model_path.glob("*.ral"))
        #
        if len(ral_files) == 0:
            print(f"Error: No .ral file found in '{self.path}'")
            return None
        elif len(ral_files) > 1:
            print(f"Error: Multiple .ral files found in '{self.path}': {[f.name for f in ral_files]}")
            return None

        self.mmdb_fname = Path(ral_files[0])

        print(f"Model file is: {self.mmdb_fname.name}")

    def set_playground(self, playground_name: str):
        """
        Validate path and, if valid, set it

        Args:
            playground_name:
        """
        if validate_path(self.path / 'playgrounds' / playground_name ):
            self.playground = playground_name

    def set_path(self, system_path: Path):
        """
        Validate path and, if valid, set it

        Args:
            system_path:
        """
        # TODO: Ensure that System is in a compatible state such as NOT_LOADED
        if validate_path(system_path):
            self.path = system_path
            # Reset local sub-paths
            # TODO: changing the path should result in a new instance of System
            self.playground = None
            self.mmdb_fname = None

    def show_playgrounds(self):
        play_path = self.path / 'playgrounds'
        pg_dirs = [f for f in play_path.iterdir() if f.is_dir()]
        for d in pg_dirs:
            print(f"  {d.name}")

    def show_active_playground(self):
        if self.playground:
            print(f"  Active playground: {self.playground}")
            return
        print("  No active playground")

    def show_path(self):
        if self.path:
            print(f"System path is: [{self.path}]")
        else:
            print(f"System path not set")

    def show_models(self, classes: list[str]):
        """
        Print out the loaded models

        Args:
            classes: A list of requested metamodel classes to view. If list is empty, entire mmdb is displayed
        """
        pass

    def load_context(self):
        """
        Tell the MX to load the context

        Returns:

        """
        pass

""" system_output.py - Process any output from the running system """

# System
from typing import TYPE_CHECKING
from pathlib import Path
import logging

# Model Integration
from mx.mxtypes import *

# MDB
if TYPE_CHECKING:
    from mdb.session import Session
from mdb.text_formatter import TextFormatter
from mdb.diagram_formatter import DiagramFormatter


class SystemOutput:

    def __init__(self, session: 'Session', sd_path: Path | None, interactive: bool, sd_theme: str | None):
        self.session = session
        self.text = TextFormatter(session)  # Initialize the sequence text output formatter
        if sd_path:
            self.theme = sd_theme or 'default'
            self.diagram = DiagramFormatter(
                session=session, sd_path=sd_path, interactive=interactive, sd_theme=self.theme)
        else:
            self.diagram = None

    def process(self, announcements: list[Announcement]):
        """
        Output the current announcements from the running system

        Args:
            announcements: A list of new announcements to report
        """
        for a in announcements:
            self.text.format_announcement(a)
            if self.diagram:
                self.diagram.format_announcement(a)
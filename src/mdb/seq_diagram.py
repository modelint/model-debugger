""" seq_diagram_output.py -- Formats and manages sequence diagram output """

# System
from pathlib import Path
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mdb.session import Session

# Model Integration
from mx.mxtypes import *
from sequins.sd_adapter import SequenceDiagramAdapter

_logger = logging.getLogger(__name__)

class SeqDiagramOutput():
    """
    This class manages the collection, formatting, and output of data to a sequence diagram generator
    """
    def __init__(self, session: 'Session', sd_path: Path, sd_theme: str, interactive: bool):

        # Sequence diagarm attributes
        self.session = session
        self.sd_path = sd_path
        self.sd_theme = sd_theme
        self.interactive = interactive
        self.sd = None

        self.lifelines: set[str] = set()  # Set of actor lifelines that have already been drawn

    def lookup_actor(self, sm_name: str, instance_id: dict[str, Any] | None) -> str | None:
        """
        Given a state machine name and an instance id, return the corresponding actor name.

        Args:
            sm_name:  State machine name
            instance_id:  Executing or partitioning instance, none if this is a single assigner state machine

        Returns:
            The actor name, None if not found
        """
        actors = self.session.active_scenario.actors
        for actor_name, actor_info in actors.items():
            if instance_id is None and actor_info.class_name == sm_name:
                # Single assigners don't have an instance ID, just match on the sm_name
                return actor_name
            if actor_info.class_name == sm_name and actor_info.instance_id == instance_id:
                return actor_name
        return None  # Actor not found

    def start(self):
        self.sd = SequenceDiagramAdapter(output_file=self.sd_path, interactive=self.interactive)
        self.sd.start_diagram(theme=self.sd_theme)

    def end(self):
        self.sd.end_diagram()

    def draw_ee_lifeline(self, actor: str):
        if actor not in self.lifelines:
            self.lifelines.add(actor)
            self.sd.add_actor(name=actor)

    def draw_inst_lifeline(self, actor: str):
        if actor not in self.lifelines:
            self.lifelines.add(actor)

        # We need to get the current state of this actor
        actor_info = self.session.active_scenario.actors[actor]
        domain = self.session.system.domains[actor_info.domain]
        current_state = domain.get_current_state(sm_name=actor_info.class_name, instance_id=actor_info.instance_id)
        created_now = actor_info.class_name in domain.lifecycle_deletion_states
        self.sd.add_actor(name=actor, initial_state=current_state, born_and_die=created_now)

    def draw_signal(self, name: str, source_actor: str, dest_actor: str, time: float):
        # `time` is the logical scenario time (seconds) computed by the execution loop; it
        # becomes the signal's depth on the chronological axis. Sequins only honors an
        # explicit depth for signals leaving a bare (external) String, which is exactly the
        # stimulus case routed here -- responses from beaded instance Strings ride their bead.
        self.sd.signal(source_actor=source_actor, dest_actor=dest_actor, name=name, time=time)

    def draw_state_entry(self, announcement: StateEntry_Announcement):
        actor = self.lookup_actor(sm_name=announcement.sm, instance_id=announcement.inst)
        self.sd.state_entered(actor, announcement.state, time=self.session.clock+.001)

        # TODO: We want to keep a clock local to the actor that starts at clock time and
        # TODO: advances .001 relative to the time of the most recent state or incoming
        # TODO: signal time directoed to this actor, whichever is the most recent

        pass

    def draw_interaction(self, i: Interaction, time: float):
        """
        Draw the interaction on the active sequence diagarm

        Args:
            i:  The interaction
            time:  Logical scenario time (seconds) at which the signal occurs
        """
        # Process source of signal
        if isinstance(i.source, ExternalAddress):
            self.draw_ee_lifeline(actor=i.source_actor)
        else:
            self.draw_inst_lifeline(actor=i.source_actor)

        # Process target of signal
        if isinstance(i.target, ExternalAddress):
            self.draw_ee_lifeline(actor=i.target_actor)
        else:
            self.draw_inst_lifeline(actor=i.target_actor)

        # Draw signal
        self.draw_signal(name=i.name, source_actor=i.source_actor, dest_actor=i.target_actor, time=time)

""" diagram_formatter.py -- Draws announcements with sequence diagram elements """

# System
from pathlib import Path
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mdb.session import Session

# Model Integration
from mx.mxtypes import *
from sequins.sd_adapter import SequenceDiagramAdapter

# MDB
from mdb.text_formatter import TextFormatter

_logger = logging.getLogger(__name__)

class DiagramFormatter():
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

        # Per-actor micro-depth: the deepest point reached on each actor's lifeline so far
        # (its latest state bead or the latest signal directed at it). Successive state
        # entries advance this by a .001 compute-time step so beads on one actor never
        # collide. This is the diagram's chronological *ordering* coordinate, distinct from
        # session.clock (real scenario seconds, which only moves on stimulus delays).
        self.actor_depth: dict[str, float] = {}

        self.start()

    def start(self):
        self.sd = SequenceDiagramAdapter(output_file=self.sd_path, interactive=self.interactive)
        self.sd.start_diagram(theme=self.sd_theme)

    def end(self):
        self.sd.end_diagram()

    def format_announcement(self, a: Announcement):
        match type(a).__name__:
            case 'mx_InteractionSignal_Announcement':
                self.draw_signal(a=a)
            case 'mx_ExternalEvent_Announcement':
                self.draw_ext_event(a=a)
            case 'mx_StateEntry_Announcement':
                self.draw_state_entry(a)

    def draw_ee_lifeline(self, actor: str):
        if actor not in self.lifelines:
            self.lifelines.add(actor)
            self.sd.add_actor(name=actor)

    def draw_inst_lifeline(self, actor: str):
        if actor not in self.lifelines:
            self.lifelines.add(actor)

            actor_info = self.session.active_scenario.actors[actor]
            domain = self.session.system.domains[actor_info.domain_alias]
            if actor_info.sm_name in domain.lifecycle_deletion_states:
                # Born-and-die instance: its first state arrives via state_entered after the
                # creation signal, so it must be introduced without an initial_state.
                self.sd.add_actor(name=actor, born_and_die=True)
            else:
                # Persistent instance: seed the lifeline with its current state.
                current_state = domain.get_current_state(sm_name=actor_info.sm_name, instance_id=actor_info.instance_id)
                self.sd.add_actor(name=actor, initial_state=current_state)

    def draw_state_entry(self, announcement: StateEntry_Announcement):
        actor = self.session.active_scenario.lookup_actor(sm_name=announcement.sm, instance_id=announcement.inst)
        # Advance this actor's lifeline by one compute-time step below its prior depth (its
        # last state, or the signal that just triggered this entry -- whichever is deeper).
        depth = self.actor_depth.get(actor, self.session.clock) + .001
        self.sd.state_entered(actor, announcement.state, time=depth)
        self.actor_depth[actor] = depth

    def draw_signal(self, a: InteractionSignal_Announcement):
        # The signal's depth is its source's current lifeline depth. Sequins only honors an
        # explicit depth for a signal leaving a bare (external) String; from a beaded
        # internal String the depth is taken from the source's projecting bead, so the value
        # we pass is ignored there and merely keeps our bookkeeping consistent.

        # Process source of signal
        if isinstance(a.source, ExternalAddress):
            source_actor = a.source.domain
            self.draw_ee_lifeline(actor=source_actor)
            src_depth = self.session.clock  # external actor has no bead; ride the macro instant
        else:
            source_actor = self.session.active_scenario.lookup_actor(
                sm_name=a.source.sm_name, instance_id=a.source.instance_id)
            self.draw_inst_lifeline(actor=source_actor)
            src_depth = self.actor_depth.get(source_actor, self.session.clock)
        # Process target of signal
        if isinstance(a.dest, ExternalAddress):
            target_actor = a.dest.domain
            self.draw_ee_lifeline(actor=target_actor)
        else:
            target_actor = self.session.active_scenario.lookup_actor(
                sm_name=a.dest.sm_name, instance_id=a.dest.instance_id)
            self.draw_inst_lifeline(actor=target_actor)

        # Raise the destination's floor so its next state bead sits below this arriving signal
        self.actor_depth[target_actor] = max(self.actor_depth.get(target_actor, self.session.clock), src_depth)

        # Add any parameters to the event string
        event_params = a.event
        if a.params:
            event_params = event_params + TextFormatter.format_params(a.params)

        # Draw signal
        if source_actor != target_actor:
            # The condition above excludes any delayed events which are self directed by nature
            self.sd.signal(source_actor=source_actor, dest_actor=target_actor, name=event_params, time=src_depth)

    def draw_ext_event(self, a: ExternalEvent_Announcement):
        """
        An external event is emitted from some state activity in a state machine actor directed to an external
        entity actor. It's time of emission matches that of the state activity.

        Args:
            a: An external event announcement produced by the mx
        """

        # Source must be an internal state machine actor
        source_actor = self.session.active_scenario.lookup_actor(
            sm_name=a.source.sm_name, instance_id=a.source.instance_id)
        self.draw_inst_lifeline(actor=source_actor)
        src_depth = self.actor_depth.get(source_actor, self.session.clock)

        # Target of signal must be an external entity actor
        self.draw_ee_lifeline(actor=a.ee)

        # Add any parameters to the event string
        event_params = a.event
        if a.params:
            event_params = event_params + TextFormatter.format_params(a.params)

        # Draw signal
        self.sd.signal(source_actor=source_actor, dest_actor=a.ee, name=event_params, time=src_depth)

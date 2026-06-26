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
        self.start()

    def start(self):
        self.sd = SequenceDiagramAdapter(output_file=self.sd_path, interactive=self.interactive)
        self.sd.start_diagram(theme=self.sd_theme)

    def end(self):
        self.sd.end_diagram()

    def format_announcement(self, a: Announcement):
        match type(a).__name__:
            case 'mx_InteractionSignal_Announcement':
                if isinstance(a.source, ExternalAddress):
                    f_signal = f"{a.source.domain} >|| {a.dest.domain_alias} : {a.event} -> "
                    f_target = self.session.active_scenario.lookup_actor(
                        sm_name=a.dest.sm_name, instance_id=a.dest.instance_id)
                    formatted_a = f_signal + f_target
                    print(f"{I1}{formatted_a}")
                else:
                    formatted_a = f"{a.source.domain_alias} >|| {a.event} -> "
                    formatted_a = formatted_a + self.format_sm_addr(a.dest)
                    print(f"{I1}{formatted_a}")
            case 'mx_ExternalEvent_Announcement':
                if a.inst:
                    inst_str = '<' + '-'.join([str(v) for v in a.inst.values()]) + '>'
                else:
                    inst_str = ""
                pstrings = [f"{n}={v[0]}" for n, v in a.params.items()]
                param_str = ', '.join(pstrings)
                formatted_a = f"{a.domain} >|| {a.ee} : {a.source}{inst_str} {a.event}( {param_str} )"
                print(f"{I1}{formatted_a}")
            case 'mx_StateEntry_Announcement':
                self.diagram.draw_state_entry(a)

    def draw_ee_lifeline(self, actor: str):
        if actor not in self.lifelines:
            self.lifelines.add(actor)
            self.sd.add_actor(name=actor)

    def draw_inst_lifeline(self, actor: str):
        if actor not in self.lifelines:
            self.lifelines.add(actor)

        # We need to get the current state of this actor
        actor_info = self.session.active_scenario.actors[actor]
        domain = self.session.system.domains[actor_info.domain_alias]
        current_state = domain.get_current_state(sm_name=actor_info.sm_name, instance_id=actor_info.instance_id)
        created_now = actor_info.sm_name in domain.lifecycle_deletion_states
        self.sd.add_actor(name=actor, initial_state=current_state, born_and_die=created_now)

    def draw_signal(self, name: str, source_actor: str, dest_actor: str, time: float):
        # `time` is the logical scenario time (seconds) computed by the execution loop; it
        # becomes the signal's depth on the chronological axis. Sequins only honors an
        # explicit depth for signals leaving a bare (external) String, which is exactly the
        # stimulus case routed here -- responses from beaded instance Strings ride their bead.
        self.sd.signal(source_actor=source_actor, dest_actor=dest_actor, name=name, time=time)

    def draw_state_entry(self, announcement: StateEntry_Announcement):
        actor = self.session.active_scenario.lookup_actor(sm_name=announcement.sm, instance_id=announcement.inst)
        self.sd.state_entered(actor, announcement.state, time=self.session.clock+.001)

        # TODO: We want to keep a clock local to the actor that starts at clock time and
        # TODO: advances .001 relative to the time of the most recent state or incoming
        # TODO: signal time directoed to this actor, whichever is the most recent

        pass

    def draw_interaction_signal(self, a: InteractionSignal_Announcement, time: float):
        # Process source of signal
        if isinstance(a.source, ExternalAddress):
            source_actor = a.source.domain
            self.draw_ee_lifeline(actor=source_actor)
        else:
            source_actor = a.source.actor
            self.draw_inst_lifeline(actor=source_actor)
        # Process target of signal
        if isinstance(a.dest, ExternalAddress):
            target_actor = a.dest.domain
            self.draw_ee_lifeline(actor=target_actor)
        else:
            target_actor = self.session.active_scenario.lookup_actor(sm_name=a.dest.sm_name, instance_id=a.dest.instance_id)
            self.draw_inst_lifeline(actor=target_actor)

        # Draw signal
        self.draw_signal(name=a.event, source_actor=source_actor, dest_actor=target_actor, time=time)


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

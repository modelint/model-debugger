""" seq_text.py - Formats scenario announcements as formatted text """

# System
from typing import TYPE_CHECKING
import logging

# Model Integration
from mx.mxtypes import *

# MDB
if TYPE_CHECKING:
    from mdb.session import Session

I1 = ' ' * 4  # Primary indent
I2 = ' ' * 2  # Secondary indent

class TextFormatter:

    def __init__(self, session: 'Session'):
        self.session = session

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
        pass
    pass

    def format_interaction(self, i: Interaction, time: float = 0.0):
        if i.action == ActionType.SIGNAL_INSTANCE:
            formatted_i = f"{i.source_actor} >|| {i.target.domain} : {i.name} -> {i.target_actor}"
        else:
            formatted_i = "Unimplemented Action Type"
        print(formatted_i)

    def format_inst_id(self, i: dict[str, Any]) -> str:
        return '<' + '-'.join([str(v) for v in i.values()]) + '>'

    def format_sm_addr(self, sm_addr: InternalAddress) -> str:
        inst_str = '<' + '-'.join([str(v) for v in sm_addr.instance_id.values()]) + '>'
        return f"{sm_addr.sm_name} {inst_str}"

    def format_params(self, params: dict[str, Any]) -> str:
        if not params:
            return ''
        pstrings = [f"{n}={v[0]}" for n, v in params.items()]
        param_str = ', '.join(pstrings)
        return f"( {param_str} )"

    def format_state_entry(self, a: Announcement):
        formatted_a = f"{a.sm} {self.format_inst_id(a.inst)} >[{a.state}]"
        print(f"{I1}{I2}{formatted_a}")

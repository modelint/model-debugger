""" seq_text.py - Formats scenario announcements as formatted text """

# System
from typing import TYPE_CHECKING
import logging

# Model Integration
from mx.mxtypes import *

# MDB
if TYPE_CHECKING:
    from mdb.session import Session

I1 = ' ' * 4  # Indent for a signal / external-event line
I2 = ' ' * 8  # Indent for a state-entry line (nested under its triggering signal)

class TextFormatter:

    def __init__(self, session: 'Session'):
        self.session = session

    def format_announcement(self, a: Announcement):
        match type(a).__name__:
            case 'mx_InteractionSignal_Announcement':
                if isinstance(a.source, ExternalAddress):
                    f_signal = f"{a.source.domain} >|| {a.dest.domain_alias} : {a.event} -> "
                    formatted_a = f_signal + TextFormatter.format_sm_addr(a.dest)
                    print(f"{I1}{formatted_a}")
                else:
                    formatted_a = f"{a.source.domain_alias} >|| {a.event} -> "
                    formatted_a = formatted_a + TextFormatter.format_sm_addr(a.dest)
                    print(f"{I1}{formatted_a}")
            case 'mx_ExternalEvent_Announcement':
                # The emitting instance now travels in a.source (an InternalAddress); display
                # its alias and instance. The instance has no space before it, per the canonical.
                inst_str = TextFormatter.format_inst_id(a.source.instance_id) if a.source.instance_id else ""
                implicit = '*' if a.implicit else ''
                formatted_a = (f"{a.domain} >|| {a.ee} : {a.source.sm_alias}{inst_str} "
                               f"{a.event}{TextFormatter.format_params(a.params)}{implicit}")
                print(f"{I1}{formatted_a}")
            case 'mx_StateEntry_Announcement':
                TextFormatter.format_state_entry(a)

    @staticmethod
    def format_interaction(i: Interaction, time: float = 0.0):
        if i.action == ActionType.SIGNAL_INSTANCE:
            formatted_i = f"{i.source_actor} >|| {i.target.domain} : {i.name} -> {i.target_actor}"
        else:
            formatted_i = "Unimplemented Action Type"
        print(formatted_i)

    @staticmethod
    def format_inst_id(i: dict[str, Any]) -> str:
        return '<' + '-'.join([str(v) for v in i.values()]) + '>'

    @staticmethod
    def format_sm_addr(sm_addr: InternalAddress) -> str:
        # A signal target is displayed by its class alias (keyletter), e.g. ASLEV <3-S1>.
        inst_str = '<' + '-'.join([str(v) for v in sm_addr.instance_id.values()]) + '>'
        return f"{sm_addr.sm_alias} {inst_str}"

    @staticmethod
    def format_params(params: dict[str, Any]) -> str:
        if not params:
            return '()'
        pstrings = [f"{n}={v[0]}" for n, v in params.items()]
        param_str = ', '.join(pstrings)
        return f"( {param_str} )"

    @staticmethod
    def format_state_entry(a: Announcement):
        formatted_a = f"{a.sm} {TextFormatter.format_inst_id(a.inst)} >[{a.state}]"
        print(f"{I2}{formatted_a}")

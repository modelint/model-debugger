"""scenario.py -- Scenario class"""

# System
from pathlib import Path
import yaml
from mx.exceptions import MXUserDBException

# Model Integration
from mx.mxtypes import *

from mdb.exceptions import MDBScenarioException

# Multipliers that normalize a declared delay to canonical seconds. The scenario yaml
# pairs a numeric `delay` with a `time` unit (see CLAUDE.md: <min, s, ms>); we fold the
# unit in here so Interaction.delay is always seconds and the execution clock can simply sum.
_TIME_UNITS = {'min': 60.0, 's': 1.0, 'ms': 0.001}

class Scenario:

    def __init__(self, sfile: Path, system=None):
        """
        Args:
            sfile: Path to a scenario yaml file
            system: The loaded System, used to resolve each domain alias to its full name
        """
        # Load the yaml file
        with open(sfile, "r") as file:
            sdata = yaml.safe_load(file)  # Load YAML content safely

        # Unpack the Actors
        self.actors = {}
        internal_actor_parse = sdata['Actors']['internal']
        for domain, instances in internal_actor_parse.items():
            # The yaml keys domains by alias (e.g. EVMAN); mx needs the full domain name
            # (e.g. Elevator Management) to resolve event-signature parameter types, and the
            # class alias (keyletter) map to fill each actor's sm_alias.
            dom = system.domains[domain] if system else None
            domain_name = dom.name if dom else None
            for name, address in instances.items():
                if sm_name := address.get('class'):
                    sm_type = StateMachineType.LIFECYCLE
                elif sm_name := address.get('rnum'):
                    if address.get('instance'):
                        sm_type = StateMachineType.MA
                    else:
                        sm_type = StateMachineType.SA
                        instance_id = None
                else:
                    msg = f"Cannot determine state machine type for internal actor in: {sfile}"
                    raise MDBScenarioException(msg)
                if sm_type != StateMachineType.SA:
                    instance_id = {attr: value for attr, value in address['instance'].items()}
                sm_alias = dom.class_aliases.get(sm_name, sm_name) if dom else sm_name
                self.actors[f"{domain}:{name}"] = InternalAddress(domain_name=domain_name, domain_alias=domain,
                                                                  sm_name=sm_name,
                                                                  sm_alias=sm_alias,
                                                                  sm_type=sm_type,
                                                                  instance_id=instance_id)

        external_actor_parse = sdata['Actors']['external']
        for ea in external_actor_parse:
            self.actors[ea] = ExternalAddress(domain=ea)
        pass

        # Unpack the interactions
        self.interactions = []
        for i in sdata['Interactions']:
            unit = i.get('time', 's')
            if unit not in _TIME_UNITS:
                raise ValueError(
                    f"Interaction '{i['description']}' has unknown time unit '{unit}'; "
                    f"expected one of {sorted(_TIME_UNITS)}"
                )
            delay_seconds = i.get('delay', 0.0) * _TIME_UNITS[unit]
            ituple = Interaction(
                description=i['description'],
                delay=delay_seconds,
                direction=Direction(i['direction']),
                action=ActionType(i['action']),
                name=i['name'],
                source=self.actors[i['source']],
                source_actor=i['source'],
                target=self.actors[i['target']],
                target_actor=i['target'],
                parameters=i.get('parameters', {})
            )
            self.interactions.append(ituple)
        pass

    def lookup_actor(self, sm_name: str, instance_id: dict[str, Any] | None) -> str | None:
        """
        Given a state machine name and an instance id, return the corresponding actor name.

        Args:
            sm_name:  State machine name
            instance_id:  Executing or partitioning instance, none if this is a single assigner state machine

        Returns:
            The actor name, None if not found
        """
        for actor_name, actor_info in self.actors.items():
            if isinstance(actor_info, ExternalAddress):
                continue  # external actors have no state machine to match against
            if instance_id is None and actor_info.sm_name == sm_name:
                # Single assigners don't have an instance ID, just match on the sm_name
                return actor_name
            if actor_info.sm_name == sm_name and actor_info.instance_id == instance_id:
                return actor_name
        return None  # Actor not found


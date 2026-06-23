"""scenario.py -- Scenario class"""

# System
from pathlib import Path
import yaml

# Model Integration
from mx.mxtypes import *

# Multipliers that normalize a declared delay to canonical seconds. The scenario yaml
# pairs a numeric `delay` with a `time` unit (see CLAUDE.md: <min, s, ms>); we fold the
# unit in here so Interaction.delay is always seconds and the execution clock can simply sum.
_TIME_UNITS = {'min': 60.0, 's': 1.0, 'ms': 0.001}

class Scenario:

    def __init__(self, sfile: Path):
        """
        Args:
            sfile: Path to a scenario yaml file
        """
        # Load the yaml file
        with open(sfile, "r") as file:
            sdata = yaml.safe_load(file)  # Load YAML content safely

        # Unpack the Actors
        self.actors = {}
        internal_actor_parse = sdata['Actors']['internal']
        for domain, instances in internal_actor_parse.items():
            for name, address in instances.items():
                instance_id = {attr: value for attr, value in address['instance'].items()}
                self.actors[f"{domain}:{name}"] = InstanceAddress(domain=domain, class_name=address['class'],
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
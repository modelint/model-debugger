"""scenario.py -- Scenario class"""

# System
from pathlib import Path
import yaml

# Model Integration
from mx.mxtypes import *

class Scenario:

    def __init__(self, sfile: Path):
        """
        Args:
            file: Path to a scenario yaml file
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
            ituple = Interaction(
                description=i['description'],
                direction=Direction(i['direction']),
                action=ActionType(i['action']),
                name=i['name'],
                source=self.actors[i['source']],
                target=self.actors[i['target']],
                parameters=i.get('parameters', {})
            )
            self.interactions.append(ituple)
        pass
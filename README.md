# Blueprint Model Debugger

<p align="center">
  <img src="https://raw.githubusercontent.com/modelint/model-debugger/main/docs/images/mdb.png"
       alt="How MDB works: a user drives mdb to run and debug scenarios against the MX execution engine, producing a sequence diagram and execution log from a system execution directory."
       width="720">
</p>

An interactive debugger for Shlaer-Mellor Executable UML models. MDB drives the
[MX model execution engine](https://github.com/modelint/model-execution) through
user-defined scenarios, letting you step through model level interactions and
inspect model properties such as current states, event queue status, and current
instance populations and such.

## Installation

```
pip install mi-mdb
```

## Usage

```
mdb [-s <system>] [-p <playground>] [-x <scenario>] [-L] [-v] [-V]
```

All path arguments are optional at launch and can be set interactively once the
debugger is running.

| Argument | Description |
|---|---|
| `-s / --system` | Path to the system directory |
| `-p / --playground` | Name of the playground to load |
| `-x / --scenario` | Name of the scenario to run (without extension) |
| `-L / --log` | Keep `mdb.log` after exit (deleted by default) |
| `-v / --verbose` | Verbose console output |
| `-V / --version` | Print version and exit |

## System directory structure

The system directory contains all artifacts needed to load and run a modeled system:

```
<system>/
    models/
        mmdb_<system>.ral        - Populated metamodel for the whole system (all modeled
                                   domains), built by the xuml_populate `popsystem` command
        <Domain>_types.yaml      - Maps a domain's data types to platform (TclRAL) types;
                                   one per modeled domain
    playgrounds/                 - A playground is like a sandbox, as many as you like
        <playground_name>/       - Define one or more scenarios and one initial population
            scenarios/
                <scenario>.yaml  - The scenario name specified as a yaml file
            population/
                <name>.sip       - Source spec for the initial instance population
                                   (instances, attribute values, initial states)
                <Domain>.ral     - A modeled domain populated with initial instances
```

MDB only needs the path to the system directory. It locates `models/` from there and hands
off to the MX engine, which reads the populated `.ral` metamodel and the per-domain type
mappings when it loads the system — MDB does not consume those files directly.

A **playground** is a named initial context — a population of instances in known states
from which scenarios are launched. Multiple playgrounds can be defined for the same system,
and multiple scenarios can be defined for each playground.

## Interactive commands

Once running, MDB presents a `# ` prompt:

```
show path                   - Show the active system path
show playgrounds            - List all playgrounds defined in the system
show playground             - Show the active playground
show scenarios              - List all scenarios for the active playground
show states                 - Display the current state of all state machines
show step                   - Show stepping mode status
show descriptions           - Show descriptions mode status
set path <abs_path>         - Set the system directory path
set playground <name_or_#>  - Select a playground by name or list number
set scenario <name_or_#>    - Select a scenario by name or list number
set step                    - Toggle stepping mode
set descriptions            - Toggle printing of interaction descriptions
execute / exec / x          - Run the active scenario
help                        - Show available commands
quit / exit                 - Exit the debugger
```

Playgrounds and scenarios can be selected by the integer shortcut shown in their listing
(e.g., `set playground 2`).

## Running a scenario

In **run-to-completion mode** (default), MDB executes the full scenario and prints each
interaction and any announcements triggered by the model engine.

In **stepping mode** (`set step`), MDB pauses after each interaction at a `>: ` prompt:

```
[enter] / n / next / s / step  - Advance to the next interaction
show states                    - Inspect current state machine states
r / run                        - Switch to run-to-completion for the remainder
q / quit / abort               - Abort the scenario
h / help / ?                   - Show stepping commands
```

## Scenario file format

Scenarios are YAML files placed in a playground's `scenarios/` directory:

```yaml
Actors:
  internal:
    <Domain>:
      <ActorName>:
        class: <ClassName>
        instance:
          <AttributeName>: <value>
  external:
    - <DomainName>

Interactions:
  - description: "Human-readable description of this step"
    direction: stimulus        # or: response
    action: signal instance    # or: external event
    name: <EventName>
    source: <Domain>:<ActorName>
    target: <Domain>:<ActorName>
    parameters:                # optional
      <ParamName>: <value>
```

Please look in the example elevator yaml file for more detailed documentation.

`stimulus` interactions inject an event into the system; `response` interactions
pass control back to the model engine and collect any announcements it emits.

## Development

For a code walkthrough of how MDB works internally — module map, control flow,
and the boundary to the MX engine — see
[documentation/internals.md](documentation/internals.md).

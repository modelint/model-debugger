# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the debugger

Activate the project virtualenv first (`/Users/starr/SDEV/Environments/ModelDebugger`), then:

```bash
python3.14 -m mdb                                      # interactive mode
python3.14 -m mdb -s <system_path> -p <playground> -x <scenario>
python3.14 -m mdb -L   # keep mdb.log after exit (default: auto-deleted)
```

All three path arguments are optional at launch; they can be set interactively with `set` commands.

## Architecture

`mdb` is an interactive CLI debugger that drives the **MX** (Model eXecutor) engine through user-defined scenarios. The overall flow is:

```
__main__.py  →  Session (REPL)  →  Scenario (YAML loader)  →  mx.System (model engine)
```

**`session.py` — `Session` singleton**
The central object. Owns the REPL (`run()`), all command handlers (`cmd_show`, `cmd_set`, `cmd_list`), and the scenario execution loop (`execute_scenario()`). During execution it calls `mx.System.inject(stimulus)` for stimulus interactions and `mx.System.go()` for response interactions, then reads `system.announcements` to display what the model engine emitted.

**`scenario.py` — `Scenario`**
Loads a YAML scenario file and parses it into a list of `Interaction` objects (from `mx.mxtypes`). Actors are resolved to typed addresses (`InstanceAddress` / `ExternalAddress`) before being stored on each interaction.

**`_dep_system.py`**
Deprecated local stub for `System`; the live implementation is `mx.system.System`. Keep this file but do not add to it.

## External dependencies (`mi-mx`, `mi-pyral`)

`mx.system.System` and `mx.mxtypes` are the primary MX interfaces:

| Type | Purpose |
|---|---|
| `System` (singleton) | Loads the `.ral` metamodel DB, exposes playgrounds, injects stimuli, collects `announcements` |
| `Interaction` (frozen dataclass) | Packages one YAML step: direction, action, source/target addresses, parameters |
| `Direction` | `STIMULUS` or `RESPONSE` |
| `ActionType` | `SIGNAL_INSTANCE` or `EXTERNAL_EVENT` |
| `InstanceAddress` | `(domain, class_name, instance_id)` namedtuple |
| `ExternalAddress` | `(domain,)` namedtuple |
| `ExternalEvent_Announcement` | `(domain, ee, source, inst, event, params)` — emitted by `ExtSignal` when `announce=True` |

`System.set_announce_triggers(['external signal'])` must be called before `execute_scenario()` so that `ExtSignal` populates `system.announcements` and returns control to the debugger after each external signal action.

## System directory layout (external to this repo)

The `--system` path points to a directory with this structure:

```
<system>/
  models/          # exactly one *.ral TclRAL metamodel database file
  playgrounds/
    <pg_name>/
      scenarios/   # *.yaml scenario files
```

## Scenario YAML format

```yaml
Actors:
  internal:
    <Domain>:
      <ActorName>:
        class: <ClassName>
        instance:
          <AttrName>: <value>
  external:
    - <DomainName>

Interactions:
  - description: "Human-readable intent"
    direction: stimulus    # or: response
    action: signal instance  # or: external event
    name: <EventName>
    source: <Domain>:<ActorName>   # key into resolved actors dict
    target: <Domain>:<ActorName>
    parameters:            # optional
      <ParamName>: <value>
```

## Interactive commands

```
show path | playground | playgrounds | scenarios | step | descriptions | states
set path <abs_path> | playground <name_or_#> | scenario <name_or_#> | step | descriptions
execute / exec / x    # run the active scenario
help / quit / exit
```

`show states` iterates all loaded domains, calls `domain.get_current_states()` (returns `list[SM_State]`), and prints each entry as `state_model <Key:Val-Key:Val> [state]`, grouped under a domain header. Domains with no active state machines are skipped. Available at both the outer `#` prompt and the inner `>:` stepping prompt.

Playgrounds and scenarios can be selected by the integer shortcut printed in their listing (1–99).

**Stepping mode** (toggled with `set step`): after each interaction the `>:` prompt appears. Commands: `[Enter]/n/next/s/step` advance, `r/run` switches to run-to-completion, `q/quit/abort` stops the scenario.
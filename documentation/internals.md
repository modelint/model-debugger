# Model Debugger — Internal Walkthrough

A developer-oriented tour of how `mdb` works under the hood. For *using* the
debugger, see `README.md` and `CLAUDE.md`. This document explains the code:
what each module does, how control flows, and where the boundary to the **MX**
(Model eXecutor) engine sits.

---

## The big picture

`mdb` is a thin interactive shell. It owns no model-execution logic of its own —
all of that lives in the external `mx` package (`mi-mx` / `mi-pyral`). `mdb`'s
job is to:

1. Let the user point at a **system** (a metamodel database + playgrounds),
2. Pick a **playground** and a **scenario**,
3. Feed that scenario's interactions into the MX engine one at a time,
4. Print back whatever the engine *announces* in response.

```
  ┌──────────────┐   ┌──────────┐   ┌────────────┐   ┌──────────────────┐
  │ __main__.py  │ → │ Session  │ → │ Scenario   │   │ mx.System        │
  │ (CLI / args) │   │ (REPL)   │   │ (YAML →    │   │ (the real engine)│
  └──────────────┘   └────┬─────┘   │ Interaction│   └────────▲─────────┘
                          │         │  objects)  │            │
                          │         └─────┬──────┘            │
                          │               │ list[Interaction] │
                          │               └───────────────────┤
                          │   inject(stimulus) / go()          │
                          └────────────────────────────────────┘
                                  reads system.announcements
```

Everything in `src/mdb/` is one of: the entry point, the session/REPL, the
scenario loader, some UI constants, or a deprecated stub.

---

## Module map

| File | Role |
|---|---|
| `__main__.py` | Entry point. Parses CLI args, sets up logging, constructs the `Session`. |
| `session.py` | The whole interactive experience: REPL, command handlers, scenario execution loop. This is the heart of the app. |
| `scenario.py` | Loads a scenario YAML file and turns it into a list of `Interaction` objects. |
| `ui_types.py` | Trivial UI constants (`CMD_PROMPT`, `STATUS`). |
| `__init__.py` | Just the version string. |
| `_dep_system.py` | **Deprecated** local stand-in for `System`. Kept for reference; not imported by the live path. Don't extend it. |

The "real" `System`, `Interaction`, `Direction`, `ActionType`, the address
namedtuples, and the announcement types all come from the external `mx` package
(`mx.system`, `mx.mxtypes`).

---

## 1. Startup — `__main__.py`

`python3.14 -m mdb` runs `main()`. The flow is short:

1. **Logging** is configured from `log.conf` (`get_logger()`). By default the
   `mdb.log` file is deleted on exit via an `atexit` hook (`clean_up()`); pass
   `-L` to keep it.
2. **Argument parsing** (`parse()`) accepts three *optional* path-ish arguments —
   `-s/--system`, `-p/--playground`, `-x/--scenario` — plus `-L`, `-v`, `-V`.
   All three locators are optional because the user can set them interactively.
3. A `Session` singleton is created and `session.initialize(...)` is called with
   whatever was supplied on the command line.

`initialize()` does *not* return until the user quits — its last act is to call
`self.run()`, the REPL. So `main()` blocks inside the session for the whole
program lifetime.

---

## 2. The Session singleton — `session.py`

`Session` is a classic singleton (`__new__` guards `_instance`, `__init__`
guards `_initialized`). There is exactly one session per process, and the rest
of the code reaches it freely.

### State it carries

- `system` — the `mx.System` instance being debugged (also a singleton).
- `playground_name`, `scenario_name` — current selections.
- `playground_scenarios` — list of scenario file stems for the active playground.
- `active_scenario` — the loaded `Scenario` object ready to run.
- `stepping` — pause between interactions? (toggled by `set step`)
- `descriptions` — print each interaction's description? (toggled by `set desc`)
- `verbose`.

### `initialize()`

Mirrors the CLI arguments into session state. If a `system_path` was given it
constructs `System()` and calls `system.initialize(...)` (which loads the
`.ral` metamodel DB). If a playground/scenario were given on the command line,
it eagerly calls `set_playground()` / `set_scenario()` so you can launch
straight into a ready-to-run state. Then it drops into `run()`.

### `run()` — the outer REPL

A plain `while True` loop reading from the `# ` prompt:

- `input()` → `shlex.split()` (so quoted args survive) → `command, *args`.
- A `match` on the lowercased command dispatches to a handler:
  `show → cmd_show`, `set → cmd_set`, `list → cmd_list`, `help → cmd_help`,
  `execute|x|exec → execute_scenario`, and `quit|exit` breaks the loop.
- Unknown commands print a hint. `EOFError`/`KeyboardInterrupt` (Ctrl-D/Ctrl-C)
  cleanly exit.

This is deliberately dumb: no readline history, no completion — just a
dispatch table.

### Command handlers

- **`cmd_show`** — read-only inspection. Notable cases:
  - `path` / `playground(s)` / `scenarios` — delegate to `system` or list helpers.
  - `step` / `descriptions` — report the current toggle state.
  - `states` — calls `show_states()` (see below).
  - (`show events` is *not* wired in here — it's only available inside the
    stepping loop; see §4.)
- **`cmd_set`** — mutation. `path`/`playground`/`scenario` change selections;
  `step`/`descriptions` *toggle* booleans and echo the new state.
- **`cmd_list`** — a stub.

### Selection helpers and the "shortcut" idiom

`show_playgrounds` / `show_scenarios` print numbered lists (`[1] - foo`). The
companion `set_playground` / `set_scenario` accept *either* the full name *or*
the integer shortcut. The conversion is `shortcut_index()`:

```python
return int(s) if re.fullmatch(r'[1-9]\d?', s) else None
```

i.e. a 1–2 digit integer with no leading zero is treated as a 1-based index into
the most recently shown list; anything else is treated as a literal name. This
is why listing and selecting are paired — the list populates the index space the
shortcut resolves against (`playground_scenarios` in particular is filled in by
`show_scenarios`).

`set_playground` additionally calls `system.load_domains(...)` (which actually
loads the playground's domains into the engine) and then re-lists scenarios.
`set_scenario` builds the path `<playground>/scenarios/<name>.yaml` and hands it
to `Scenario(...)`, storing the result in `active_scenario`.

### Inspection: `show_states` and `show_events`

Both iterate `self.system.domains` and ask each `Domain` for live engine state:

- `show_states()` → `domain.get_current_states()` → `list[SM_State]`. Prints
  `state_model <Key:Val-Key:Val> [state]` grouped under a domain header; domains
  with no active state machines are skipped.
- `show_events()` → `domain.get_pending_events()` → `dict[str, list[SM_Pending]]`.
  For each SM instance with anything pending it prints an `I -` line
  (interaction events) and/or a `C -` line (completion event), formatting
  parameters as `name: value`.

These are pure presentation over engine-provided namedtuples
(`SM_State`, `SM_Pending`) — `mdb` doesn't model state itself.

---

## 3. Scenario loading — `scenario.py`

`Scenario(sfile)` reads a YAML file (`yaml.safe_load`) and produces
`self.interactions`, a `list[Interaction]`. Two phases:

### Resolve actors → typed addresses

The YAML `Actors` section names participants; the loader turns each into a
typed address namedtuple from `mx.mxtypes`, keyed by `"<Domain>:<Name>"`:

- **internal** actors → `InstanceAddress(domain, class_name, instance_id)`,
  where `instance_id` is the dict of identifying attribute values.
- **external** actors → `ExternalAddress(domain)`.

The resulting `actors` dict is the lookup table for the next phase.

### Build interactions

Each entry under `Interactions` becomes a frozen `Interaction` dataclass:

```python
Interaction(
    description=...,                 # human-readable intent
    direction=Direction(i['direction']),   # "stimulus" | "response"
    action=ActionType(i['action']),        # "signal instance" | "external event"
    name=i['name'],                        # event name
    source=actors[i['source']],            # resolved to an address
    target=actors[i['target']],
    parameters=i.get('parameters', {}),
)
```

Note the string-to-enum coercion (`Direction(...)`, `ActionType(...)`) and the
`source`/`target` lookups into the `actors` table. After this, the scenario is a
plain ordered list of fully-typed interactions, decoupled from the YAML.

> The `pass` statements at the end of each loop are leftover no-ops, harmless.

---

## 4. Running a scenario — `execute_scenario()`

This is the most important method in the project. It walks the active scenario's
interactions and drives the engine.

### Setup

```python
System.set_announce_triggers(['external signal'])
```

This tells MX to (a) populate `system.announcements` whenever an *external
signal* fires, and (b) return control to the debugger after each such action.
Without this, the engine would run ahead and we'd never get to display
intermediate responses. (This is a *static* method on `System` — a global engine
setting, not per-instance.)

### The loop

The interactions are walked with an explicit iterator so the same `next(...)`
call can be reused from several places:

```python
interactions = iter(self.active_scenario.interactions)
i = next(interactions, None)
while i is not None:
    ...
```

For each interaction `i`:

- If `descriptions` is on, print `i.description`.
- **Dispatch on direction:**
  - `STIMULUS` → print the formatted interaction (`format_interaction`), then
    `system.inject(stimulus=i)` — this hands control to MX, which runs until the
    next announce trigger. Then `format_announcements(system.announcements)`
    prints whatever the engine emitted.
  - `RESPONSE` → there's nothing to inject, so `system.go()` simply resumes the
    engine, then again we print any announcements.

> **Known gap (documented in-code):** announcements emitted by a stimulus are
> *not* correlated with the `response` interactions the scenario declares. The
> scenario still lists expected responses, but matching them to actual
> announcements is left for a future testing layer. For now responses just
> nudge the engine forward.

### Stepping vs. run-to-completion

- If `stepping` is **off**, the loop immediately advances (`i = next(...)`).
- If `stepping` is **on**, an inner loop blocks on the `>: ` prompt so you can
  inspect engine state *between* interactions:
  - `[Enter] / n / next / s / step` → advance one interaction.
  - `r / run` → flip `stepping` off and continue to completion.
  - `q / quit / abort` → stop the scenario.
  - `show states` / `show events` → call the inspection helpers in place.
  - `h / ? / help` → list these.

This is the only place `show events` is reachable — it's an
inside-the-run inspection command, by design.

### Output formatting helpers

- `format_interaction(i)` — renders a `SIGNAL_INSTANCE` stimulus as
  `source.domain >|| target.domain : name -> class <inst>`. Other action types
  are unimplemented (prints a placeholder).
- `format_announcements(...)` — renders each `ExternalEvent_Announcement` as
  `domain >|| ee : source<inst> event( params )`. The `>||` glyph is a
  visual "signal crossing a domain boundary" marker.

---

## 5. The MX boundary — what `mdb` relies on

Everything `mdb` knows about the engine is reached through a small surface. If
you're maintaining `mdb`, these are the contracts you depend on:

### From `mx.system.System` (a singleton)

| Member | Used for |
|---|---|
| `initialize(system_path, verbose)` | Load the `.ral` metamodel DB. |
| `load_domains(playground)` | Populate `system.domains` for a playground. |
| `domains: dict[str, Domain]` | Iterated by `show_states` / `show_events`. |
| `playgrounds` / `available_playgrounds` | Listing & shortcut resolution. |
| `playground` | The active playground path. |
| `inject(stimulus: Interaction)` | Run a stimulus into the engine. |
| `go()` | Resume the engine with no stimulus (response steps). |
| `announcements: list[Announcement]` | What the engine emitted; read after each step. |
| `set_announce_triggers([...])` *(static)* | Configure when MX pauses & announces. |
| `set_path`, `show_path`, `show_active_playground` | Misc. inspection/mutation. |
| `Domain.get_current_states()` → `list[SM_State]` | State inspection. |
| `Domain.get_pending_events()` → `dict[str, list[SM_Pending]]` | Event inspection. |

### From `mx.mxtypes`

- `Interaction` (frozen dataclass) — the unit of scenario execution.
- `Direction` (`STIMULUS` / `RESPONSE`) and `ActionType`
  (`SIGNAL_INSTANCE` / `EXTERNAL_EVENT`).
- `InstanceAddress`, `ExternalAddress` (and `AssignerAddress`) — actor addresses.
- `SM_State`, `SM_Pending` — namedtuples returned by the inspection calls.
- `ExternalEvent_Announcement` / `InteractionSignal_Announcement` — the
  announcement variants; only the external-event variant is formatted today.

---

## 6. Control-flow summary (one stimulus)

A single `stimulus` interaction during `execute`:

```
user: execute
  Session.execute_scenario()
    System.set_announce_triggers(['external signal'])   # once, up front
    loop → i (STIMULUS, signal instance)
      Session.format_interaction(i)        # "A >|| B : Ev -> Class <id>"
      System.inject(stimulus=i)            # control → MX engine
        ... engine runs state machines until an external signal fires ...
        ... engine fills system.announcements, returns control ...
      Session.format_announcements(system.announcements)
      if stepping: prompt ">:"             # inspect via show states / show events
      i = next(...)                        # advance
```

That cycle — *format → inject/go → read announcements → (optionally) pause* — is
the entire execution model.

---

## 7. Things to know before you change something

- **Two singletons** (`Session`, `System`) are reached globally. Don't construct
  second instances expecting fresh state.
- **`_dep_system.py` is dead code** — the live `System` is `mx.system.System`.
  Read it only as historical context; don't add to it (per `CLAUDE.md`).
- **`show events` lives only in the stepping loop**, not in `cmd_show`. If you
  want it at the outer prompt, wire it into `cmd_show` explicitly.
- **Shortcuts depend on a prior listing.** `set scenario 2` only works after the
  scenario list has been shown (it fills `playground_scenarios`). Selecting a
  playground re-shows scenarios, which is what keeps the index space fresh.
- **Stimulus/response correlation is intentionally absent.** Don't assume
  declared `response` interactions are validated against engine announcements —
  they aren't yet (see the in-code TODO in `execute_scenario`).
- **The `>||` glyph** in formatted output denotes a signal crossing a domain
  boundary; it's cosmetic.

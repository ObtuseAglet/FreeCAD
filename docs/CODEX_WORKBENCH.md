# Codex Workbench Integration

This fork adds a new FreeCAD module at `src/Mod/Codex` that integrates
Codex CLI into the UI for in-app model generation.

## What It Adds

- `Codex` workbench in the workbench selector.
- `Generate 3D with Codex` command.
- Prompt dialog for natural-language requests.
- Optional inclusion of current selection context.
- Script preview/edit step before execution.
- Transactional execution with undo/redo support.
- Preferences path for runtime settings:
  - `User parameter:BaseApp/Preferences/Mod/Codex/CliPath`
  - `User parameter:BaseApp/Preferences/Mod/Codex/Model`
  - `User parameter:BaseApp/Preferences/Mod/Codex/TimeoutSeconds`
  - `User parameter:BaseApp/Preferences/Mod/Codex/DryRun`

## Build

`BUILD_CODEX` is now available and defaults to `ON`.

Example configure command:

```bash
cmake -S . -B build -DBUILD_GUI=ON -DBUILD_CODEX=ON
```

## Usage

1. Launch the built FreeCAD.
2. Switch to the `Codex` workbench.
3. Click `Generate 3D with Codex`.
4. Describe the object or operation you want.
5. Review/edit generated Python and run it.

## Runtime Requirements

- `codex` CLI must be installed and authenticated.
- If `codex` is not on `PATH`, set one of:
  - Environment variable: `FREECAD_CODEX_CLI`
  - Preference key: `CliPath` under `BaseApp/Preferences/Mod/Codex`

## Notes

- Generated scripts run locally inside FreeCAD and can modify the active
  document.
- Set `DryRun=true` to generate/preview without executing scripts.

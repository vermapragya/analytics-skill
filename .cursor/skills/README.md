# Cursor Skills Pointer

This file exists so Cursor recognizes this repo as a skills source.

## Where the canonical skills live

The actual skills live in `../../skills/` at the repo root, not here. Each skill is a folder with a `SKILL.md` file.

## To use these skills in your own project

```bash
# from inside this repo
bash install.sh --target cursor --project-dir /path/to/your/project
```

This copies all skills into `<your-project>/.cursor/skills/`.

## To use these skills personally (all Cursor projects)

```bash
bash install.sh --target cursor
```

This copies all skills into `~/.cursor/skills/`.

See `../../INSTALL.md` for full options.

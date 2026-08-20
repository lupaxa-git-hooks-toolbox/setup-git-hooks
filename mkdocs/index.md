# Setup Git Hooks

A pip-installable CLI. Each consuming repo lists hook sources in
`hooks/<type>-config.yml`. `setup-hooks` fetches `src/<type>` from those
remotes and writes `hooks/<type>/01-<filename>`. The multiplexer is
installed into Git's hooks directory unless you skip it.

## What it does

- Reads one YAML file per hook type (`hooks/pre-commit-config.yml`, …)
- Resolves `HEAD`, `LATEST`, a semver tag, or a full commit SHA
- Copies the hook file from `src/<type>` in each source repo
- Prefixes names from YAML list order so the multiplexer run order is defined
- Installs the multiplexer from `hooks/multiplexer-config.yml`
- Appends a `.gitignore` rule for generated scripts

## Next steps

- [Getting started](getting-started.md) — install and first run
- [Usage](usage.md) — flags, re-runs, and gitignore
- [Reference](reference.md) — YAML fields, versions, and exits
- [Examples](examples.md) — a pre-commit config

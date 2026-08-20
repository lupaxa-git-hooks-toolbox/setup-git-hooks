# Getting started

## Requirements

- Python 3.13 or newer
- `git` on `PATH`
- A Git working tree for the consuming repo

## Install the CLI

```bash
python -m pip install lupaxa-setup-git-hooks
```

From this checkout:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Add YAML

Create `hooks/pre-commit-config.yml` and `hooks/multiplexer-config.yml` in
the consuming repository. List order is run order.

```yaml
- name: Hello one
  filename: hello-one
  url: https://github.com/lupaxa-git-hooks-toolbox/test-pre-commit-1
  version: HEAD
```

```yaml
url: https://github.com/lupaxa-git-hooks-toolbox/git-hooks-multiplexer
version: HEAD
```

Each hook source repo ships one file at `src/<type>` (for example
`src/pre-commit`). The pre-commit template repo is a starter for new
hook repos, not something to list here.

## First run

```bash
setup-hooks
```

That writes `hooks/pre-commit/01-hello-one`, installs the multiplexer as
the `pre-commit` Git hook, and appends `hooks/*/*` to `.gitignore`.
Generated scripts stay local. Re-run with `--force` to replace them.
Each hook shows `Installing <name> -> <path>` on one line (yellow, with a
cyan spinner on a TTY), then that line becomes `Installed ...` in green.

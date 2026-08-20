# Usage

## Commands

```bash
setup-hooks
setup-hooks -t pre-commit
setup-hooks --force
setup-hooks --skip-multiplexer
setup-hooks --skip-gitignore
setup-hooks --list-hook-types
```

With no `--hook-type`, every `hooks/*-config.yml` except
`hooks/multiplexer-config.yml` is installed.

Each hook updates one line: yellow `Installing <name> -> <path>` with a
cyan spinner, then the same line turns green `Installed ...`. Failures
turn that line red. `--force` first prints that generated scripts are
being replaced. `-v` adds the source URL and version.

## Re-runs

If generated scripts already exist under `hooks/<type>/`, the command
fails and writes nothing. Pass `--force` to delete those `NN-*` files
and reinstall from the YAML. Config files are never deleted.

## Multiplexer

Install is on by default. `hooks/multiplexer-config.yml` is then
required. `--skip-multiplexer` skips both the require and the copy.
The multiplexer file comes from `src/multiplexer` in the listed repo
and is written to Git's hooks directory for that type.

## Gitignore

After a successful type install, `setup-hooks` appends this unless you
pass `--skip-gitignore`:

```gitignore
# Git Hooks Toolbox — generated subhooks
hooks/*/*
```

Configs stay at `hooks/<type>-config.yml` and
`hooks/multiplexer-config.yml`. If `.gitignore` cannot be updated, the
scripts are already installed: the snippet is printed and the command
still exits 0.

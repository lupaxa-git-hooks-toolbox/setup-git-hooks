<p align="center">
    <a href="https://github.com/lupaxa-git-hooks-toolbox">
        <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/organisations/git-hooks-toolbox/readme-logo.png" alt="Organisation Logo" />
    </a>
</p>

<h1 align="center">Setup Git Hooks</h1>

Install Git Hooks Toolbox subhooks into a local clone. Each repo lists hook
sources in `hooks/<type>-config.yml`. Running `setup-hooks` fetches
`src/<type>` from those remotes and writes `hooks/<type>/01-<filename>`.
The multiplexer is installed into `.git/hooks/<type>` unless you skip it.

Python 3.13 or newer, `git` on `PATH`, and a Git working tree.

## Install

```bash
python -m pip install lupaxa-setup-git-hooks
```

From this checkout:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
make init
```

## Configure

Create `hooks/pre-commit-config.yml` and `hooks/multiplexer-config.yml` in
the consuming repository. List order is run order. Each source repo ships
one file at `src/<type>` (for example `src/pre-commit`). The pre-commit
template repo is a starter for new hook repos, not something to list here.

```yaml
# hooks/pre-commit-config.yml
- name: Hello one
  filename: hello-one
  url: https://github.com/lupaxa-git-hooks-toolbox/test-pre-commit-1
  version: HEAD
- name: Hello two
  filename: hello-two
  url: https://github.com/lupaxa-git-hooks-toolbox/test-pre-commit-2
  version: LATEST
- name: Hello three
  filename: hello-three
  url: https://github.com/lupaxa-git-hooks-toolbox/test-pre-commit-3
  version: v0.1.0
```

```yaml
# hooks/multiplexer-config.yml
url: https://github.com/lupaxa-git-hooks-toolbox/git-hooks-multiplexer
version: LATEST
```

That writes `hooks/pre-commit/01-hello-one`, `02-hello-two`, and
`03-hello-three`. Point the multiplexer YAML at a fork when you maintain
your own. `name` is the log label only. `filename` is the destination
basename (`^[A-Za-z0-9._-]+$`); the installed name is `NN-<filename>`
(`01`–`99`). Duplicate filenames in one file are an error.

| Version          | Resolution                                                      |
| :--------------- | :-------------------------------------------------------------- |
| `HEAD`           | Default branch (`git ls-remote --symref`)                       |
| `LATEST`         | Newest semver tag; finals rank above pre-releases of that X.Y.Z |
| Semver tag       | Optional `v` / `V` prefix. Must exist as a tag                  |
| 40-character SHA | Full SHA-1. Short SHAs are rejected                             |

Resolution and fetch use git only. Private remotes use your existing
credentials.

### Pin a Commit

Use a full 40-character SHA. Short SHAs are rejected.

```yaml
# hooks/pre-commit-config.yml
- name: Hello one
  filename: hello-one
  url: https://github.com/lupaxa-git-hooks-toolbox/test-pre-commit-1
  version: b0114a98e8c8ef0b1db5bd5c03c0321363d91da3
```

## Run

From the consuming repository root. With no `--hook-type`, every
`hooks/*-config.yml` except `hooks/multiplexer-config.yml` is installed.

```bash
setup-hooks
setup-hooks --force
setup-hooks --skip-multiplexer
setup-hooks --skip-gitignore
setup-hooks -t pre-commit
setup-hooks --list-hook-types
```

`hooks/multiplexer-config.yml` is required unless `--skip-multiplexer`.
The multiplexer file comes from `src/multiplexer` in the listed repo and
is written to Git's hooks directory for that type.

Each hook updates one line from `Installing ... -> <path>` to
`Installed ...` (cyan spinner, yellow then green on a TTY; red on
failure). `-v` adds the source URL and version. Generated scripts are
not committed. If they already exist, the command fails and writes
nothing. Re-run with `--force` to delete those `NN-*` files and
reinstall. Config files are never deleted.

After a successful type install, this is appended unless you pass
`--skip-gitignore`:

```gitignore
# Git Hooks Toolbox — generated subhooks
hooks/*/*
```

Configs stay at `hooks/<type>-config.yml` and
`hooks/multiplexer-config.yml`. If `.gitignore` cannot be updated, the
scripts are already installed: the snippet is printed and the command
still exits 0.

| Flag                      | Default        | Meaning                                                                  |
| :------------------------ | :------------- | :----------------------------------------------------------------------- |
| `-t`, `--hook-type`       | all discovered | Install only this type                                                   |
| `--force`                 | off            | Clear generated scripts for the type, then reinstall                     |
| `--skip-multiplexer`      | off            | Do not require or install the multiplexer                                |
| `--skip-gitignore`        | off            | Do not edit `.gitignore`                                                 |
| `-l`, `--list-hook-types` | off            | Print types discovered from `hooks/*-config.yml` (except mux) and exit 0 |
| `-v`, `--verbose`         | off            | Include source URL and version in the Installing line                    |

A missing work tree, invalid YAML, a bad version, a missing multiplexer
config, or existing generated scripts without `--force` exits non-zero
before fetch. A missing remote ref fails that type; earlier types in the
same run stay. A gitignore update failure still exits 0.

<a href="https://github.com/the-lupaxa-project">
  <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/components/footer-for-child-orgs.svg" alt="The Lupaxa Project Footer" width="100%" />
</a>

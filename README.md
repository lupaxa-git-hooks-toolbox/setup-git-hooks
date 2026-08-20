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

## Install

Python 3.13 or newer.

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

## Run

From the consuming repository root:

```bash
setup-hooks
setup-hooks --force
setup-hooks --skip-multiplexer
setup-hooks --skip-gitignore
setup-hooks -t pre-commit
```

`hooks/multiplexer-config.yml` is required unless `--skip-multiplexer`.
Each hook updates one line from `Installing ... -> <path>` to
`Installed ...` (cyan spinner, yellow then green on a TTY). Generated
scripts are not committed. Re-run with `--force` to replace them.

## Documentation

The guide is in [`mkdocs/`](mkdocs/index.md). After installing the `dev`
extras:

```bash
make mkdocs-serve
```

<a href="https://github.com/the-lupaxa-project">
  <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/components/footer-for-child-orgs.svg" alt="The Lupaxa Project Footer" width="100%" />
</a>

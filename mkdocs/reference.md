# Reference

## CLI flags

| Flag                      | Default        | Meaning                                                                  |
| :------------------------ | :------------- | :----------------------------------------------------------------------- |
| `-t`, `--hook-type`       | all discovered | Install only this type                                                   |
| `--force`                 | off            | Clear generated scripts for the type, then reinstall                     |
| `--skip-multiplexer`      | off            | Do not require or install the multiplexer                                |
| `--skip-gitignore`        | off            | Do not edit `.gitignore`                                                 |
| `-l`, `--list-hook-types` | off            | Print types discovered from `hooks/*-config.yml` (except mux) and exit 0 |
| `-v`, `--verbose`         | off            | Include source URL and version in the Installing line                    |

## Hook type YAML

`hooks/<type>-config.yml` is a list. Order is run order.

| Field      | Required | Meaning                                                          |
| :--------- | :------- | :--------------------------------------------------------------- |
| `name`     | yes      | Human label for logs only                                        |
| `filename` | yes      | Destination basename (no prefix). Single path segment            |
| `url`      | yes      | Git remote URL (`https://` or `git@`)                            |
| `version`  | yes      | `HEAD`, `LATEST`, semver tag, or 40-character hex SHA            |

`filename` matches `^[A-Za-z0-9._-]+$`. The installed name is
`NN-<filename>` (`01-` … `99-`). Duplicate filenames in one file are
an error. The source blob is always `src/<type>`.

## Multiplexer YAML

`hooks/multiplexer-config.yml` is one mapping:

| Field     | Required | Meaning                              |
| :-------- | :------- | :----------------------------------- |
| `url`     | yes      | Git remote URL of the multiplexer    |
| `version` | yes      | Same version grammar as hook entries |

The source blob is always `src/multiplexer`.

## Version

| Value            | Resolution                                                      |
| :--------------- | :-------------------------------------------------------------- |
| `HEAD`           | Default branch (`git ls-remote --symref`)                       |
| `LATEST`         | Newest semver tag; finals rank above pre-releases of that X.Y.Z |
| Semver tag       | Optional `v` / `V` prefix. Must exist as a tag                  |
| 40-character SHA | Full SHA-1. Short SHAs are rejected                             |

Resolution and fetch use git only. Private remotes use your existing
credentials.

## Exits

| Situation                                              | Result                                                                 |
| :----------------------------------------------------- | :--------------------------------------------------------------------- |
| Not a git work tree / invalid YAML / bad version form  | Non-zero before fetch                                                  |
| Mux on and `multiplexer-config.yml` missing            | Non-zero before fetch                                                  |
| Generated scripts exist, no `--force`                  | Non-zero; no writes                                                    |
| Missing remote ref or missing `src/<type>`             | Fail that type. Earlier types in the same run stay                     |
| Gitignore update fails                                 | Scripts already installed; snippet printed; exit 0                     |

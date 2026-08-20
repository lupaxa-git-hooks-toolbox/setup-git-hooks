# Examples

## Pre-commit list

YAML list order becomes `01-`, `02-`, …

```yaml
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

That writes `hooks/pre-commit/01-hello-one`,
`hooks/pre-commit/02-hello-two`, and `hooks/pre-commit/03-hello-three`.

## Pin a commit

```yaml
- name: Hello one
  filename: hello-one
  url: https://github.com/lupaxa-git-hooks-toolbox/test-pre-commit-1
  version: b0114a98e8c8ef0b1db5bd5c03c0321363d91da3
```

## Multiplexer

```yaml
url: https://github.com/lupaxa-git-hooks-toolbox/git-hooks-multiplexer
version: HEAD
```

Point `hooks/multiplexer-config.yml` at a fork when you maintain your
own multiplexer. Use `HEAD` until that repo has a semver tag.

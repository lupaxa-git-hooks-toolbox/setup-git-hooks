from __future__ import annotations

import argparse
import sys

from setup_hooks.config import ConfigError, discover_hook_types
from setup_hooks.git import GitError, core_hooks_path, git_hooks_dir, work_tree_root
from setup_hooks.gitignore import GITIGNORE_SNIPPET, GitignoreError, ensure_gitignore
from setup_hooks.install import InstallError, install_hook_type
from setup_hooks.progress import Progress


def setup_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="setup-hooks",
        description="Install Git Hooks Toolbox subhooks from per-type YAML.",
    )
    parser.add_argument(
        "-t",
        "--hook-type",
        default=None,
        help="Install only this hook type (default: all discovered types).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Clear generated scripts for the type, then reinstall.",
    )
    parser.add_argument(
        "--skip-multiplexer",
        action="store_true",
        help="Do not require or install the multiplexer.",
    )
    parser.add_argument(
        "--skip-gitignore",
        action="store_true",
        help="Do not edit .gitignore.",
    )
    parser.add_argument(
        "-l",
        "--list-hook-types",
        action="store_true",
        help="Print discovered hook types and exit.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print extra progress on stderr (source URL and version).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = setup_arg_parser().parse_args(argv)
    try:
        root = work_tree_root()
        dest_hooks = git_hooks_dir(root)
    except GitError as exc:
        print(exc, file=sys.stderr)
        return 1

    configured = core_hooks_path(root)
    if configured:
        print(
            f"Warning: core.hooksPath is set to {configured}; "
            f"writing the multiplexer to {dest_hooks}.",
            file=sys.stderr,
        )

    hooks_dir = root / "hooks"
    types = discover_hook_types(hooks_dir)
    if args.list_hook_types:
        for hook_type in types:
            print(hook_type)
        return 0

    if args.hook_type:
        types = [args.hook_type]
    if not types:
        print("No hook type configs found under hooks/.", file=sys.stderr)
        return 1

    progress = Progress(verbose=args.verbose)
    try:
        for hook_type in types:
            try:
                install_hook_type(
                    root,
                    hook_type,
                    force=args.force,
                    skip_multiplexer=args.skip_multiplexer,
                    skip_gitignore=True,
                    hooks_dir=dest_hooks,
                    progress=progress,
                )
            except (InstallError, ConfigError, GitError) as exc:
                if not progress.failed:
                    progress.fail(str(exc))
                return 1
            if not args.skip_gitignore:
                try:
                    ensure_gitignore(root)
                except GitignoreError as exc:
                    print(exc, file=sys.stderr)
                    print("Add this to .gitignore:", file=sys.stderr)
                    print(GITIGNORE_SNIPPET, end="", file=sys.stderr)
    finally:
        progress.close()
    return 0


def run() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    run()

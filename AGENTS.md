# Repository instructions for coding agents

## General instructions

- Read and follow [`.github/copilot-instructions.md`](.github/copilot-instructions.md) before changing code or
  documentation. It defines the repository's conventions for British English, docstrings, imports, formatting,
  naming, Markdown, and issue reporting.
- Work from the repository root.
- On Windows development host Use the `django-dev` Conda environment at ` C:\Users\gavin\.conda\envs\django-dev` for Python and Django commands.
- Preserve unrelated changes in the working tree.

## Available commands

The root `Makefile` provides the standard development commands:

- `make check` runs Django's system checks.
- `make black` runs import sorting, Django template formatting, and Black with the repository's 119-character line
  length.
- `make test` runs the pytest suite against the pre-provisioned PostgreSQL test database.
- `make isort` sorts Python imports.
- `make djhtml` formats Django HTML templates.
- `make spell` checks Python spelling with `codespell`.
- `make restart` restarts the `labman` systemd service.

## Required workflow

After changing code:

1. Run the relevant focused tests.
2. Run `make black` to apply the repository's formatting rules.
3. Run `make check` and any relevant broader tests.
4. Run `make restart` so the system services hosting the web application load the changes.
5. Confirm that the `labman` service restarted successfully.

`make restart` invokes `sudo systemctl restart labman` and may require elevated permissions.

Do not run `make commit`. It invokes `git commit -a` without a commit message, which opens an interactive editor, and
it also pushes automatically. If the user explicitly requests a commit or push, use suitable non-interactive Git
commands and keep staging, committing, and pushing as separate operations.

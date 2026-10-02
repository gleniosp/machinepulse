# MachinePulse

MachinePulse is an open-source, simulation-first condition-monitoring platform
for rotating machinery.

## Quick start

Install [mise](https://mise.jdx.dev/) and run these commands from the repository
root:

```sh
mise run setup
mise run check
```

`setup` installs the locked tools and Python environment, then configures the
pre-commit hook. `check` runs the checks currently available in the repository.
See the [developer tooling baseline](docs/developer-tooling.md) for the command
interface and ownership details.

## GitHub CLI

We pin GitHub CLI (`gh`) with mise because project work uses GitHub issues,
milestones, and pull requests to track task state. `mise run setup` installs
the shared version; authentication stays in your user environment.

Run `gh auth login` for browser-based sign-in, or `gh auth login --with-token`
with a classic personal access token. For a fine-grained token, set `GH_TOKEN`
in the current terminal; GitHub CLI prefers it over saved credentials:

```bash
# Enter the token when prompted; input is hidden.
read -s GH_TOKEN
export GH_TOKEN
```

Scope the token to only the `gleniosp/machinepulse` repository to limit its
reach, and grant these repository permissions:

| Permission    | Access         |
| ------------- | -------------- |
| Contents      | Read and write |
| Issues        | Read and write |
| Pull requests | Read and write |
| Metadata      | Read-only      |

For token details, see GitHub CLI's [`GH_TOKEN` documentation](https://cli.github.com/manual/gh_help_environment), [fine-grained token guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens), and [permission reference](https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens).

## Project documentation

The end-to-end monitoring workflow is not available yet. See:

- [Documentation hub](docs/README.md) — document map and current project status.
- [Product vision](docs/product/vision.md) — purpose, users, and principles.
- [Product scope](docs/product/scope.md) — version 0.1 boundaries and non-goals.
- [Architecture overview](docs/architecture/overview.md) — system shape and evolution.
- [Project governance](docs/project-governance.md) — contribution, security, and provenance guidance.

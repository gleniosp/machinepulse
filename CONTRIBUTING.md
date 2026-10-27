# Contributing to MachinePulse

This guide is provisional. MachinePulse is in heavy development and is currently
maintainer-led: interfaces, architecture details, and development workflows may
change without compatibility guarantees. Broader contributions are expected
once the initial implementation phases are in place.

Trying the project and reporting problems are useful now. Before starting a
substantial contribution, open or comment on a
[GitHub issue](https://github.com/gleniosp/machinepulse/issues) to discuss the
approach and confirm scope with the maintainer. The
[roadmap](docs/roadmap.md) points to milestones and issues; an open issue is not
necessarily ready for implementation.

## Try it or report a problem

Use the [Docker quickstart](docs/guides/docker-quickstart.md) to try the current
components. Downloading the public source and running it locally do not require
GitHub authentication.

For a bug report, include what you expected, what happened, the source revision,
relevant commands, and your OS and Docker versions. Include a small reproduction
and logs when possible. Keep credentials and private data out of reports.
The [new issue chooser](https://github.com/gleniosp/machinepulse/issues/new/choose)
provides guided forms for bug reports and feature proposals. Please use the
form that best fits your report or idea.

## Develop an agreed change

Follow the [developer setup and checks](docs/developer-tooling.md#root-setup-and-tasks)
for mise, the locked environments, and Git hooks. From the repository root:

```sh
cp .env.example .env
mise run setup
mise run check
```

Run the relevant integration or Docker checks when changing those paths; the
[tooling guide](docs/developer-tooling.md) lists commands and prerequisites.
Explain what changed and provide validation results in the pull request.

The [working agreement](docs/working-agreement.md#git-and-repository-hygiene)
owns branch, commit, review, and issue-completion conventions for maintainer-agent
work. Coordinate with the maintainer on the delivery branch and keep commits
focused. GitHub issues own implementation checklists; the repository holds
specifications and supporting evidence. Update end-user documentation when
behavior or setup changes. Follow the
[artifact provenance and licensing baseline](docs/project-governance.md#artifact-provenance-and-licensing)
for code, data, models, and images.

Use the [PR template](.github/pull_request_template.md) when preparing a change
for review. The [commit-message check](docs/developer-tooling.md#commit-message-validation)
runs automatically after hook setup and can also check a prepared message file.
The [formatting and editor guide](docs/developer-tooling.md#formatting-and-editor-support)
describes formatter ownership and the recommended VS Code extensions.

## GitHub CLI (optional)

GitHub's web interface is sufficient for reports and contribution discussions.
For CLI-based issue and pull-request work, `mise run setup` installs the pinned
`gh` version. Authenticate separately in your user environment:

```sh
mise exec -- gh auth login
mise exec -- gh auth status
```

The [login command](https://cli.github.com/manual/gh_auth_login) supports browser
sign-in or a classic personal access token through `--with-token`. For a
fine-grained token, GitHub CLI recommends supplying `GH_TOKEN`; it takes
precedence over saved credentials. In Bash or Zsh, enter it without echoing it:

```sh
read -s GH_TOKEN
export GH_TOKEN
```

For maintainer automation, restrict the token to this repository and grant only
the permissions needed for the operations you intend to perform:

| Operation              | Repository permission         |
| ---------------------- | ----------------------------- |
| Read workflow runs     | Actions: read                 |
| Push source changes    | Contents: read and write      |
| Maintain issues        | Issues: read and write        |
| Maintain pull requests | Pull requests: read and write |
| Repository metadata    | Metadata: read                |

This table describes maintainer operations, not access required to try the
project or report a problem. See the official
[environment variable reference](https://cli.github.com/manual/gh_help_environment),
[token guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens),
and [permission reference](https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens).
Keep tokens in your user environment, outside repository files and `.env`.

# Project Governance and Artifact Licensing

- **Status:** Accepted baseline
- **Related task:** P00-009
- **Project license:** Apache-2.0, recorded in the repository [LICENSE](../LICENSE)

## License decision

MachinePulse source code and project-authored technical documentation are
intended to use Apache-2.0 unless a file or artifact states a different
license. The repository license does not grant permission to use project names,
trademarks, or third-party materials.

## Governance follow-ups

- `CONTRIBUTING.md`: document branch, commit, pull-request, review, testing,
  and provenance expectations before accepting outside contributions.
- `CODE_OF_CONDUCT.md`: adopt a contributor conduct policy and identify the
  maintainers responsible for reports.
- `SECURITY.md`: define private vulnerability reporting, supported versions,
  disclosure handling, and security-sensitive data rules.
- Issue and pull-request templates: add once the first runtime implementation
  workflow exists.
- Dependency and license review: record third-party software licenses and
  notices before distribution.

## Artifact provenance and licensing

- **Source code:** Apache-2.0 unless explicitly marked otherwise.
- **Documentation:** Apache-2.0 for project-authored material unless explicitly
  marked otherwise; quoted or adapted external material must retain attribution
  and compatible licensing.
- **Datasets and generated data:** record generator version, configuration, seed,
  source revision, and license or provenance. Do not add proprietary or
  unlicensed data.
- **Models and analytical artifacts:** record training/evaluation data
  provenance, model license, code revision, and known restrictions.
- **Images and plots:** use project-generated or clearly licensed material,
  retain attribution where required, and record the source license.

These policies are a repository baseline, not a substitute for legal review of
specific third-party materials or distribution arrangements.

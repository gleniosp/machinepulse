# Engineering Journal

The engineering journal is the chronological record of building and learning through MachinePulse. It records what happened and the evidence for it; it does not replace product specifications, task acceptance criteria, or ADRs.

## What belongs here

Record:

- what was planned for the day;
- what was actually completed;
- what was learned;
- unexpected behavior and failed approaches;
- decisions made or questions discovered;
- links to code, tests, plots, benchmarks, ADRs, and experiments; and
- what should change in the next plan.

The journal should be honest about uncertainty and limitations. It is acceptable for an approach to fail if the result and lesson are documented clearly.

## Weekly cadence

Each implementation week has one Markdown file with:

- a weekly objective;
- five small implementation days;
- expected evidence;
- a blog-post outline;
- a weekly review; and
- links to related specs and tasks.

Work outside the numbered phases may use a separate dated notes file, such as
the [public-onboarding notes](public-onboarding.md), linked to its GitHub issue
and milestone. Record evidence there without duplicating task checklists.

Week 00 is the documentation and project-foundation week. Week 01 begins runtime implementation.

## Daily entry guidance

A daily entry should answer:

1. What did I intend to do?
2. What did I actually do?
3. What evidence proves it?
4. What did I learn?
5. What changed in the plan?
6. What is the smallest useful next step?

Prefer links to artifacts over claims. Examples include test commands, plots, benchmark output, schema fixtures, and experiment records.

## Public-repository hygiene

Everything committed to this journal is public. Do not include:

- secrets or credentials;
- private contact information;
- proprietary or sensitive data;
- unlicensed external material; or
- unverified claims presented as product behavior.

## Journal status

Existing weekly statuses describe the recorded evidence at the time of writing;
they are not live task or milestone state. New entries link to GitHub for scope
and delivery progress and record dated observations and validation results.
Follow the [working agreement](../working-agreement.md) for issue closure.

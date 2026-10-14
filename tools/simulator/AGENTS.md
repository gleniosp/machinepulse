# Simulator guidance

- `src/machinepulse_simulator/` contains the Python package; `tests/` contains
  tests and golden fixtures; `experiments/` contains reproducible experiment
  runners.
- `pyproject.toml` owns package metadata, runtime dependencies
  (`project.dependencies`), build configuration, and Python tooling config.
  This project's `mise.toml` owns its task names; its tasks use the repository
  root as their working directory and the shared root Pixi environment. Commit
  the root `pixi.lock`. `.pixi/` at the repository root is local environment
  state.
- Use the repository's mise-provided Pixi CLI, then run native checks from this
  folder with the root manifest: `pixi run --manifest-path ../../pixi.toml
  --locked -e dev pytest`, `pixi run --manifest-path ../../pixi.toml --locked
  -e dev ruff check src tests experiments`, `pixi run --manifest-path
  ../../pixi.toml --locked -e dev mypy src tests experiments`, and `pixi run
  --manifest-path ../../pixi.toml --locked -e dev ruff format --check src
  tests experiments`.
- Run `mise run simulator:experiment:vibration` from the repository root to
  regenerate the EXP-0001 vibration plots and summaries.
- The Pixi `default` environment is for runtime use; `dev` adds test and quality
  tools. In VS Code, use `.pixi/envs/dev` at the repository root; if VS Code
  already selected another interpreter, select the Pixi interpreter explicitly.
- Add concise, accurate docstrings to Python modules, classes, functions, and
  methods. Use Google style for functions and methods; document `Args` and
  `Returns` whenever applicable, and include exceptions when they clarify the
  public behavior.
- Avoid empty or docstring-only `__init__.py` files unless package semantics
  require them; prefer namespace packages for tests and fixture directories.
- Simulator behavior is synthetic and non-diagnostic; follow
  [`docs/specs/simulator.md`](../../docs/specs/simulator.md) and keep ground truth
  separate from telemetry.

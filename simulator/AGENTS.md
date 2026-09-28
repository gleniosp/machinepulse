# Simulator guidance

- `src/machinepulse_simulator/` contains the Python package; `tests/` contains
  tests and golden fixtures.
- `pyproject.toml` owns runtime dependencies (`project.dependencies`), Pixi's
  `dev` feature, tasks, and Python tooling config. `pixi.lock` is committed;
  `.pixi/` is local environment state.
- Use the repository's mise-provided Pixi CLI, then run tasks from this folder:
  `pixi run -e dev test`, `pixi run -e dev lint`,
  `pixi run -e dev typecheck`, and `pixi run -e dev format-check`.
- The Pixi `default` environment is for runtime use; `dev` adds test and quality
  tools. In VS Code, use `simulator/.pixi/envs/dev`; if VS Code already selected
  another interpreter, select the Pixi interpreter explicitly.
- Add concise, accurate docstrings to Python modules, classes, functions, and
  methods. Use Google style for functions and methods; document `Args` and
  `Returns` whenever applicable, and include exceptions when they clarify the
  public behavior.
- Avoid empty or docstring-only `__init__.py` files unless package semantics
  require them; prefer namespace packages for tests and fixture directories.
- Simulator behavior is synthetic and non-diagnostic; follow
  [`docs/specs/simulator.md`](../docs/specs/simulator.md) and keep ground truth
  separate from telemetry.

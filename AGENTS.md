# AGENTS.md

A README for coding agents working in this repo (Claude Code, Cursor, etc.) -- see https://agents.md for the format this follows.

## Project overview

`genai-portfolio` is a personal portfolio of generative AI projects, experiments, and notes. Each project lives in its own folder under `projects/`.

## Setup

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Conventions

- One project per folder under `projects/`, each with its own README describing problem, approach, and results
- Keep notebooks in `notebooks/`, longer write-ups/architecture notes in `docs/`
- Prefer clear structure and documentation over cleverness -- this repo exists partly to demonstrate professional engineering habits

## Git workflow

- Never commit directly to `main`. Branch as `feat/<project>-<topic>` / `fix/<project>-<topic>` / `chore/<topic>` and open a PR; PRs are squash-merged.
- Commit messages: Conventional Commits with the project as scope -- `feat(resume-app): ...`, `fix(resume-app): ...`, `test(resume-app): ...`, `chore(repo): ...` for repo-wide changes. One logical change per commit.
- Before committing: `pre-commit run --all-files` (gitleaks, ruff, hygiene) and the project's tests (`cd projects/resume-app && python -m pytest -q`).
- Releases: tag milestones as `<project>/vX.Y.Z` (e.g. `resume-app/v0.2.0`) and create a GitHub Release with notes.
- Never commit secrets or session state (`.env`, `data/linkedin_session.json`). Lint rules live in `ruff.toml`.

## Testing gotchas

- Tests must never reach a live LLM. When a test calls `importlib.reload(llm_client)`, reload BEFORE `patch(...)` -- reloading afterwards discards the mock and makes a real call to LM Studio on localhost:1234 (passes on a dev Mac with LM Studio running, fails in CI).

## Active project

`projects/resume-app/` -- an agentic AI resume-tailoring app built with the Claude Agent SDK. See its own README for scope and status.

## Notes for agents

This file is intentionally thin right now -- add to it as you learn things about this repo that aren't obvious from the code (build quirks, gotchas, decisions). Treat every avoidable repeat mistake as a signal to update this file.

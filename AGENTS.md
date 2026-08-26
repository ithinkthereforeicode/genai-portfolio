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

## Active project

`projects/resume-app/` -- an agentic AI resume-tailoring app built with the Claude Agent SDK. See its own README for scope and status.

## Notes for agents

This file is intentionally thin right now -- add to it as you learn things about this repo that aren't obvious from the code (build quirks, gotchas, decisions). Treat every avoidable repeat mistake as a signal to update this file.

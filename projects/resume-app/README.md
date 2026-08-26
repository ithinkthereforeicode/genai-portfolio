# Resume App

An agentic AI application for working with resumes -- tailoring a resume to a specific job description, scoring fit, and surfacing gaps. Built as a hands-on project for developing deep agentic AI skills: the agent loop, tool use, and harness design.

## Status

Early scoping -- build starting now.

## Goals

- Learn agentic AI fundamentals hands-on: tool use, the agent loop, and harness design (state management, guardrails, observability, context handling)
- Produce a working, demoable tool: given a resume and a job description, tailor/score/suggest edits
- Document the build well enough that it doubles as an interview talking point

## Planned stack

- Claude Agent SDK (Python or TypeScript) for the agent loop, tools, and most of the harness plumbing (sessions, hooks, permissions, MCP)
- Built and iterated on in Cursor / Claude Code

## Structure (planned)

```
resume-app/
  README.md
  src/            # agent + tool implementations
  tests/
  docs/           # architecture notes, harness design decisions
```

## Why this project

Part of a broader push to build deep, hands-on agentic AI skills -- see the rest of this portfolio one level up.

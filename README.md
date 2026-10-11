# GenAI Portfolio

[![resume-app CI](https://github.com/ithinkthereforeicode/genai-portfolio/actions/workflows/resume-app-ci.yml/badge.svg)](https://github.com/ithinkthereforeicode/genai-portfolio/actions/workflows/resume-app-ci.yml)
[![lint](https://github.com/ithinkthereforeicode/genai-portfolio/actions/workflows/lint.yml/badge.svg)](https://github.com/ithinkthereforeicode/genai-portfolio/actions/workflows/lint.yml)

A collection of generative AI projects, experiments, and notes — built to practice and demonstrate professional software engineering habits (clean structure, documentation, and version control) while exploring GenAI.

## Structure

```
genai-portfolio/
├── projects/       # Standalone projects, one folder per project
├── notebooks/       # Exploratory notebooks / experiments
├── docs/             # Notes, write-ups, architecture diagrams
└── README.md
```

## Projects

- **[resume-app](projects/resume-app/)** -- an agentic AI resume-tailoring tool, built to develop hands-on agentic AI / harness-design skills.

More projects coming soon -- each gets its own folder with a README describing the problem, approach, and results.

## Setup

```bash
git clone https://github.com/ithinkthereforeicode/genai-portfolio.git
cd genai-portfolio
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pre-commit && pre-commit install   # secret scan + lint on every commit
```

## Development workflow

- **Branch per change.** `main` is protected; work happens on short-lived branches (`feat/<project>-<topic>`, `fix/<project>-<topic>`) merged by squash-merge pull request.
- **Conventional commits, scoped by project:** `feat(resume-app): add LinkedIn session reuse`, `fix(resume-app): ...`, `chore(repo): ...`.
- **CI on every PR:** each project's tests run in GitHub Actions, and the same pre-commit hooks (gitleaks secret scan, ruff, hygiene checks) run in the `lint` workflow.
- **Milestone tags per project:** `<project>/vMAJOR.MINOR.PATCH` (e.g. `resume-app/v0.1.0`) with a GitHub Release describing what shipped.

## License

MIT — see [LICENSE](LICENSE).

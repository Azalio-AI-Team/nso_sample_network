# Agent Guidelines

See the complete agent instructions and Spec-Driven Development guide in [AGENTS.md](./AGENTS.md).
See the comprehensive repository package and architecture catalog in [PACKAGES.md](./PACKAGES.md).

## Quick Reference

- **Spec Kit Constitution**: [`.specify/memory/constitution.md`](.specify/memory/constitution.md)
- **Repository Package Catalog**: [`PACKAGES.md`](./PACKAGES.md)
- **Active Integrations**: Antigravity (`agy`), Claude Code (`claude`)
- **Repository Workflow**: `network-sdd` (invoked via `/speckit-network-workflow`)
- **Key Pipeline Steps**:
  1. `/speckit-clarify` — Ask clarifications to understand the requirement
  2. `/speckit-specify` — Structure requirements and acceptance criteria
  3. Codebase Discovery — Review `PACKAGES.md` for affected modules/YANG models
  4. `/speckit-plan` — Formulate technical plan, code diffs, and generate network test payloads
  5. Impact & Payload Review Checkpoint
  6. **Human Approval Gate** — Mandatory sign-off by human engineer before implementation
  7. `/speckit-tasks` & `/speckit-implement` — Systematic implementation against offline mock tests
  8. `/speckit-converge` — Convergence verification
- **Quality & Linting**: `ruff check .`
- **Tests**: `uv run python -m unittest discover tests`

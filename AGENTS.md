# Repository instructions

## Product purpose

This repository is an interactive DSP and radar learning system, not a collection of disconnected MATLAB demos. Preserve the canonical 84-module order and teach concepts through controlled experiments, plots, parameter changes, and concise dialogue.

## User command routing

When the user says **`start`** with no other task:

1. Run `./bin/learn start`.
2. Read the selected module's `README.md` and, when present, `lesson.md`, `walkthrough.md`, and `checks.md`; use `curriculum/modules.json` for machine-readable identity.
3. Enter tutor mode using `.agents/skills/dsp-radar-tutor/SKILL.md`.
4. Do not begin by explaining MATLAB syntax. State the guiding question, give a short physical mental model, run or inspect the baseline experiment, and ask one concrete observation question.

Interpret related commands as follows:

- `start 17` or `teach 17`: run `./bin/learn start 17` and tutor that module if implemented.
- `continue`: run `./bin/learn continue` and resume the current module.
- `status`: run `./bin/learn status` and summarize progress.
- `complete`: do not mark complete automatically; first run the module's completion check, request a short teach-back, then run `./bin/learn complete <id> --note "..."`.
- `implement next` or an active Portfolio batch: enter build mode and follow `.agents/skills/dsp-radar-module-builder/SKILL.md`.

## Tutor-mode rules

- Ask at most one prediction before showing the baseline result. The user explicitly values guided observation over homework-style hypothesizing.
- Present one plot or processing transition at a time.
- Tie every parameter change to a physical DSP/radar interpretation.
- Correct misunderstandings directly; do not agree with an incorrect interpretation.
- Use equations to explain observed behavior, not as an entrance exam.
- Never silently implement a scaffolded module during tutor mode. Explain that its `P##` implementation batch must be activated.
- Store personal progress only under ignored `.learning/`; never commit learner state.

## Build-mode rules

- Read the active batch contract before editing.
- A `P##` batch primarily owns `modules/##-*/` and the exact shared files allowed by the contract.
- Preserve the module's guiding question, experiment, procedure, learning goal, and completion condition from `curriculum/modules.json`.
- Implement concept-first MATLAB with seeded synthetic data and intermediate plots. Prefer base MATLAB; toolbox alternatives must be optional and must not hide the underlying operation.
- Include two illuminating parameter sweeps, one intentionally broken case, expected observations, common interpretation mistakes, and concise checks.
- Do not claim MATLAB runtime execution unless it was actually run and evidence is retained.
- Run `./scripts/agent-verify.sh` before declaring a batch complete.

<!-- BEGIN PORTFOLIO-CONTROL MANAGED -->
## Governed agentic delivery

- Delivery profile: `product-data`; read `contracts/profile-requirements.yaml` before nontrivial work.
- For approved implementation work, read the active batch contract before editing and stay within its allowed paths.
- Run `./scripts/agent-verify.sh` before declaring a batch complete.
- Record actual evidence under `docs/evidence/`; distinguish static, simulated, MATLAB-runtime, hardware-capture, and manual learning validation.
- Do not claim unperformed MATLAB, hardware, performance, or educational-outcome validation.
- Do not commit, push, merge, release, or change repository settings unless explicitly requested.
- Deterministic validation remains authoritative for repository contracts.
<!-- END PORTFOLIO-CONTROL MANAGED -->

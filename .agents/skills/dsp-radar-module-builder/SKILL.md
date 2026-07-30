---
name: dsp-radar-module-builder
description: Implement one approved P## DSP/radar curriculum batch with MATLAB experiment, lesson, walkthrough, checks, validation, and evidence while preserving the canonical module contract.
---

# DSP and Radar Module Builder

## Required inputs

- Active Portfolio Control batch contract.
- Canonical entry in `curriculum/modules.json`.
- Existing module `README.md`, including its AI prompt.
- Dependencies listed in the batch and prior implemented modules when relevant.

## Deliverables

For the active module, create or complete:

- `experiment.m`: one runnable, sectioned, seeded experiment with intermediate plots.
- `lesson.md`: concise physical explanation, equations tied to the plots, and prerequisite links.
- `walkthrough.md`: baseline, two parameter sweeps, one broken case, expected observations, and recovery.
- `checks.md`: observation checks, interpretation checks, and a short teach-back rubric.
- `curriculum/modules.json`: active module status and validation updated accurately.
- tests or deterministic static validation appropriate to the module.
- retained batch evidence describing exactly what ran and what did not.

## Implementation constraints

- Prefer base MATLAB and explicit operations before toolbox convenience functions.
- Do not make syntax instruction the learning objective.
- Do not hide the main operation behind an opaque helper.
- Keep figures purposeful and label units and axes.
- Use deterministic random seeds.
- Do not claim a script was executed in MATLAB if only static checks ran.
- Do not alter another module unless the active batch explicitly allows a shared correction.

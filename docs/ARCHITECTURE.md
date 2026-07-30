# Architecture

## Canonical layers

1. `curriculum/modules.json` owns immutable project identity and the manual-derived learning contract.
2. `modules/` owns human-readable module materials and implemented MATLAB experiments.
3. `bin/learn` owns local selection and progress state under ignored `.learning/`.
4. `.agents/skills/` owns Codex tutor and module-builder behavior.
5. `kpbianco/portfolio-control/products/dsp-radar-learning/` owns roadmap, acceptance, risk, and one approved implementation batch per project.

## Separation of concerns

Tutor mode consumes implemented content and may update only local learner state. Build mode changes repository content only under an approved batch. Curriculum identity cannot drift merely because a generated experiment is revised.

## Evidence boundary

Repository CI proves static structure and CLI behavior. Numerical MATLAB correctness requires named runtime evidence. Personal learning completion requires a manual teach-back and is intentionally not a repository release claim.

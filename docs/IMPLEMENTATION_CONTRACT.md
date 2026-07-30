# Module Implementation Contract

A module may change from `scaffolded` to `implemented` only when it contains:

- a self-contained seeded `experiment.m`;
- intermediate plots with units and meaningful labels;
- a concept-focused `lesson.md`;
- a `walkthrough.md` containing a baseline, two parameter sweeps, and one broken case;
- a `checks.md` file with observation, interpretation, and teach-back checks;
- deterministic repository validation;
- retained evidence stating whether MATLAB actually ran.

Placeholder prose, a toolbox demo copied without explanation, or a script that jumps directly to a final plot does not satisfy the contract.

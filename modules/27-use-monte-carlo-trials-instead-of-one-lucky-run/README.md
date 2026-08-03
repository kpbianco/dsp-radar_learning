# P27: Use Monte Carlo Trials Instead of One Lucky Run

**Phase 3: Modulation, Channels, and Statistical Estimation**  
**Status:** Implemented by governed batch `P27`

## Guiding question

Why is one noise realization not enough to judge an algorithm?

## Experiment

Send known BPSK symbols through independent additive white Gaussian noise,
apply an explicit unit-energy matched filter, and record whether each hard
decision is correct. Compare the empirical bit-error probability with the
analytic AWGN result over thousands of independent trials.

## Procedure

Plot individual error outcomes, running error probability, a 95% Wilson
confidence interval, and the final empirical distributions. Sweep trial count
and energy-per-bit to noise-density ratio while holding all other inputs fixed.
Then deliberately reuse one lucky noise realization as if it were thousands of
independent trials, diagnose the false certainty, and recover with a clean
private-seed rerun.

## What this should teach

Random algorithms must be characterized statistically. A reproducible seed
makes a run auditable; it does not make one realization representative.
Independent trials, uncertainty intervals, and enough error events prevent a
lucky example from becoming an unsupported performance claim.

## Completion condition

Your reported BER approaches the analytic reference as the independent trial
count grows, the confidence interval narrows without being mistaken for a
guarantee, and a rerun with seed 2701 exactly reproduces the retained outcomes.

## Prerequisites and dependencies

- P23 supplies the BPSK symbol and hard-decision picture.
- P24 supplies the matched-filter interpretation.
- P27 uses base MATLAB only. It does not require Communications Toolbox,
  Statistics and Machine Learning Toolbox, files, network access, or hardware.

## Run the lesson

```bash
./bin/learn start 27
```

Then run `experiment.m` from this folder and follow `walkthrough.md` one
observation at a time. Use `checks.md` for the final interpretation and
teach-back.

## Files

- `experiment.m` — seeded BPSK Monte Carlo experiment, two sweeps, broken
  pseudo-replication case, and deterministic recovery
- `lesson.md` — physical/statistical model, equations, limits, and mistakes
- `walkthrough.md` — guided baseline, controlled changes, failure, and recovery
- `checks.md` — observation, prediction, operational, and teach-back checks

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Use the implemented P27 artifacts
to guide one plot or processing transition at a time. Begin with the question
“Why is one noise realization not enough to judge an algorithm?”, give a short
physical model of repeated noisy BPSK measurements, inspect the independent-
trial baseline, and ask one concrete observation question. Tie every trial-
count or Eb/N0 change to error-probability uncertainty rather than MATLAB
syntax. Include the deliberately reused-noise case, correct any claim that
zero observed errors proves zero BER, and finish with the teach-back in
`checks.md`.

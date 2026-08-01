# P07: Understand Convolution as Echo Addition

**Phase 1: Signals, Sampling, and Systems**  
**Status:** Implemented by batch `P07`

## Guiding question

What is convolution actually doing at each output sample?

## Experiment

Use a short pulse and a three-tap echo channel whose taps have visibly different delays and amplitudes.

## Procedure

Construct the output first by shifting and scaling copies of the input, then by convolution. Animate the overlap-and-sum process for a small sequence.

## What this should teach

Convolution is not an abstract command; it adds delayed, scaled contributions from the input according to the system response.

## Completion condition

You can manually predict the main peaks in the convolved output.

## Run the lab

```bash
./bin/learn start 7
```

Run `experiment.m` in base MATLAB, then use `walkthrough.md` and `checks.md` to
connect each plotted shifted copy to one term in the convolution sum. The
experiment writes no files and uses no toolbox, helper function, external data,
network, device, or service. It uses a private deterministic seed, preserves the
global random stream and unrelated figures, bounds all loops and animation
frames, and creates or replaces only its named workspace variables and
P07-tagged figures.

## Dependency and operation contract

P06 is the prerequisite. The baseline uses a short pulse and an explicit
three-tap real echo channel. It first constructs every delayed, scaled echo copy
and adds those copies sample by sample. A second nested-loop implementation
evaluates the convolution equation directly; only then does base MATLAB `conv`
serve as a numerical cross-check. The bounded small-sequence animation exposes
the products entering one output sample at a time. No essential operation is
hidden behind `filter`, a toolbox channel object, or another black box.

The script contains two one-variable sweeps—middle-path delay and third-path
signed gain—and an intentionally broken overwrite-instead-of-add case with a
documented recovery. Static repository checks do not imply that MATLAB or the
figures ran.

Batch rollback removes the four implementation artifacts and P07 tests/evidence,
restores this brief and public catalog wording, and must restore only P07
manifest status to `scaffolded`. It does not alter learner state or P06.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Understand Convolution as Echo Addition". The guiding question is: "What is convolution actually doing at each output sample?" Use this experiment: Use a short pulse and a three-tap echo channel whose taps have visibly different delays and amplitudes. Have me perform these actions: Construct the output first by shifting and scaling copies of the input, then by convolution. Animate the overlap-and-sum process for a small sequence. The main concept I must learn is: Convolution is not an abstract command; it adds delayed, scaled contributions from the input according to the system response. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`

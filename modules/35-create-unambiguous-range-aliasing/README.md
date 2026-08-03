# P35: Create Unambiguous-Range Aliasing

**Phase 4: Pulsed and Pulse-Doppler Radar Foundations**  
**Status:** Implemented by batch `P35`

## Guiding question

Why can a distant target appear at a shorter false range?

## Experiment

Simulate a periodic pulse train and a target whose round-trip delay exceeds one
pulse-repetition interval. Keep the transmit-pulse identity visible on an
absolute timeline, then deliberately discard that identity to form the range
reported inside one listening interval.

## Procedure

Observe the baseline echo arriving after two newer transmissions. Sweep pulse
repetition frequency (PRF) at fixed true range, then sweep true range at fixed
PRF. Plot the unambiguous interval and the folded apparent range. Finally use
the original pulse label as an intentionally unavailable shortcut, reject that
result, and recover the receiver's modulo-range result exactly.

## What this should teach

PRF sets an unambiguous range because pulse identity becomes uncertain when
echoes arrive after the next transmission. A fixed-PRF receiver reports
`R_app = mod(R_true, c/(2*PRF))`; that fold is not a change in propagation
speed, range resolution, or target position.

## Completion condition

You can calculate the folded apparent range for a target beyond the unambiguous interval.

## Prerequisites and dependencies

- Complete P34 first so single-pulse delay/Doppler mismatch is familiar. P35
  adds repetition and pulse identity; its folded listening interval is not an
  ambiguity-function surface.
- P30's monostatic conversion `R = c*tau/2` is used explicitly, and P31's
  distinction between resolution and accuracy remains in force.
- Run in base MATLAB. No toolbox, hardware, file input, network access, or
  external data is required. A private seed creates only a faint repeatable
  noise floor; the alias calculation itself is deterministic.

## Start the implemented lesson

```bash
./bin/learn start 35
```

Run `experiment.m`, then use `walkthrough.md` and `checks.md` to interpret one
plot and one parameter change at a time.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Create Unambiguous-Range Aliasing". The guiding question is: "Why can a distant target appear at a shorter false range?" Use this experiment: Simulate periodic pulses and a target whose round-trip delay exceeds one pulse-repetition interval. Have me perform these actions: Vary PRF and target range. Fold received echoes into successive listening intervals and plot apparent versus true range. The main concept I must learn is: PRF sets an unambiguous range because pulse identity becomes uncertain when echoes arrive after the next transmission. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Implemented files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`

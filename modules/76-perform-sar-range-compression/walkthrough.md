# Walkthrough: from long echoes to complex range histories

Keep the guiding question visible: **What information is created before azimuth focusing begins?**
Run `experiment.m` from this module directory. Move
through one figure or processing transition at a time.

## 1. Baseline waveform and one look

In Figure 1, inspect the I/Q chirp and its linear instantaneous-frequency
sweep. Then compare the center aperture position's raw and compressed range
profiles.

Expected observation: each raw target return occupies the 2 microsecond pulse
extent, while the matched output is localized near one slant range. The printed
range-grid spacing is 1.25 m and the 20 MHz nominal resolution is 7.5 m; those
numbers describe different things.

Concrete observation question: which trace makes the three target delays
easier to identify, and what operation created that change?

## 2. Preserve the aperture dimension

Inspect Figure 2, the raw magnitude matrix. The vertical coordinate is
platform cross-range position; it is not target cross-range. Each row is one
independent radar look, and the long chirps overlap in fast time.

Now inspect Figure 3. The upper panel is the range-compressed magnitude matrix.
Targets form localized slant-range ridges, but no aperture rows have been
summed. The lower panel compares one target's unwrapped complex ridge phase
with its expected two-way path phase.

Expected observation: range compression sharpens the horizontal range
coordinate while preserving the phase variation down the aperture. This
complex matrix—not the magnitude picture alone—is the information passed to
azimuth focusing.

## 3. Sweep 1: change only bandwidth

Figure 4 compares 10, 20, and 40 MHz isolated-target responses. Pulse duration,
sample rate, target delay, and the rest of the model stay fixed.

Expected observation: measured full -3 dB width decreases monotonically as
bandwidth increases, following the `c/(2B)` trend. The curves are sampled
finite-duration LFM responses, so measured width need not equal the simple
nominal scale exactly.

Prediction before rerun: if you changed only the middle bandwidth from 20 to
30 MHz, should its response width move toward the 10 MHz or 40 MHz curve?

Restore the reviewed bandwidth list before continuing so the assertions and
retained metrics describe the canonical experiment.

## 4. Sweep 2: change only target range spacing

Figure 5 uses two equal-amplitude, equal-phase targets and the unchanged 20 MHz
waveform. Only their perpendicular-range separation changes: 3.75, 10, then
15 m.

Expected observation: the closest pair merges, the middle pair is still not
separated by the reviewed -3 dB valley rule, and the 15 m pair is clearly
separated. Target spacing does not change the waveform's resolution; it tests
whether the fixed resolution is sufficient for this scene.

Do not call the two peaks cross-range resolution. This operation has not
focused aperture phase.

## 5. Intentionally broken case: keep magnitude, discard phase

Figure 6 first uses `abs(range_compressed_history)`. The magnitude ridges are
exactly preserved, but the broken ridge phase is zero rather than the expected
path-dependent curve. Its printed phase coherence must fall below 0.20.

This is the trap: a convincing range image can still be unusable for coherent
azimuth focus. Magnitude says where energy arrived in fast time; it does not
retain the sign and angle of I/Q rotation.

## 6. Recovery from unchanged complex data

The recovery does not regenerate the scene or invent missing phase. It uses
the retained complex range-compressed matrix, asserts exact equality with the
pre-failure data, and recovers phase coherence above 0.98.

Expected observation: recovered phase follows the expected two-way path while
the range magnitudes remain identical to the broken display. The next SAR
stage can use this phase, but P76 does not perform that focus.

## 7. Connect the processing chain

- P32 explained why LFM bandwidth compresses delay response.
- P37 made the fast-time/slow-time matrix axes explicit.
- P75 showed why moving one antenna creates a coherent phase history.
- P76 compresses each fast-time row while retaining that history.
- P77 will compensate path length and combine aperture rows.
- P78 will expose and correct range-cell migration.

The compact answer to the guiding question is: **before azimuth focusing, SAR
range compression creates localized slant-range histories whose complex
samples still carry coherent aperture phase.**

## Cancellation, recovery, and rollback

The script has finite loops, immutable sample ceilings, six tagged figure
groups, no worker, no timer, no background task, no file/network write, and no
external transaction. If you need cancellation, press Ctrl+C. Rerun from the
top; P76 closes only figures tagged `P76`, recreates private seed 7601 without
changing MATLAB's global random state, and rebuilds all data deterministically.

Repository rollback is batch-local: restore the scaffold README, remove the
four added lesson artifacts, focused test, and evidence, change only P76's
manifest status to `scaffolded`, and restore P76's public catalog lines. Keep
P75, later module identities and statuses, managed contracts, and personal
`.learning/` state untouched.

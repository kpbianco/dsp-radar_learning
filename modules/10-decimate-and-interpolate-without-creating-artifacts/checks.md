# P10 Checks — Decimate and Interpolate Without Creating Artifacts

## Guiding question

Why must filtering accompany sample-rate changes?

## Baseline observation checks

Use the unchanged baseline and the `results` structure.

1. Confirm `fs_low_hz` is 600 samples/s and `new_nyquist_hz` is 300 Hz.
2. Identify the original lines at 90 Hz and 420 Hz.
3. Confirm `alias_high_hz` is 180 Hz and that
   `naive_alias_amplitude_v` is visibly larger than
   `filtered_alias_amplitude_v`.
4. Identify the first interpolation image at `first_image_hz = 510` Hz.
5. Confirm the reconstruction filter reduces that image while restoring the
   90 Hz component toward its original one-volt amplitude.

## Predict, then verify

Answer each in one sentence before reading the relevant sweep or changing the
control.

1. If the high tone moves from 280 Hz to 340 Hz while the 600-sample/s output
   rate stays fixed, which low-rate frequency will the naive path show?
2. If the anti-alias FIR is moved after sample dropping, can it distinguish an
   original 420 Hz tone from a genuine 180 Hz tone?
3. If zeros are inserted but the reconstruction FIR is omitted, will the 90 Hz
   baseband line be the only spectral copy?
4. If the reconstruction FIR gain is one instead of four, what happens to the
   retained tone amplitude?
5. If reconstruction tap count increases with all other controls fixed, which
   improves and what costs increase?

Expected concise answers: 260 Hz; no; no; it stays near one quarter amplitude;
image rejection sharpens while delay and arithmetic work increase.

## Interpretation checks

Mark each true or false and correct every false statement.

- Dropping samples destroys out-of-band energy before it can alias.
- A low-rate 180 Hz component can represent the original 420 Hz baseline tone.
- Anti-alias filtering after decimation is equivalent to filtering before it.
- Zero insertion changes the grid and creates spectral images but adds no new
  information.
- Reconstruction filtering must follow zero insertion and include interpolation
  gain to restore passband amplitude.
- The applicable design boundary for decimation is original Nyquist, not new
  Nyquist.
- A finite FIR needs transition margin, so a tone just below new Nyquist can be
  attenuated even though it has not aliased.

The correct sequence is false, true, false, true, true, false, true.

## Failure classification

For each symptom, name the mechanism and recovery.

| Symptom | Mechanism | Recovery |
| --- | --- | --- |
| 420 Hz becomes 180 Hz at 600 samples/s | Aliasing during naive decimation | Low-pass below new Nyquist before selecting samples |
| Copies appear at 510, 690 Hz, and beyond | Imaging from zero insertion | Gain-scaled reconstruction low-pass after insertion |
| Desired output is near one quarter amplitude | Missing interpolation gain | Scale reconstruction-filter DC gain by four |
| Last good figures remain after an assertion | Fail-fast validation before figure replacement | Correct the malformed bounded control and rerun |
| A foreground plot call is interrupted | User cancellation, not algorithm state corruption | Ctrl+C and deterministic rerun; no persistent recovery needed |

## Isolation, compatibility, and resource checks

- Verify only figures tagged `P10` are replaced and no file or learner state is
  written.
- Verify the script uses a private `RandStream`, so running it does not alter
  the global random stream.
- Verify the FIR coefficient formula, accumulation, sample selection, and zero
  insertion are visible rather than hidden by a multirate or filter toolbox.
- Keep the record at or below 4800 samples, filters at or below 129 taps, each
  sweep at or below eight cases, and figures at five groups.
- There is no asynchronous operation, timeout API, migration, service,
  database, hardware, network, or device state in this module. Cancellation is
  a foreground Ctrl+C followed by a deterministic rerun.

## Teach-back completion

In two or three sentences, answer the guiding question and use both baseline
numbers: explain why 420 Hz becomes 180 Hz without prefiltering, why zero
insertion creates a 510 Hz image, and where each filter belongs. A complete
teach-back must distinguish irreversible aliasing from removable interpolation
images and must not claim that interpolation recreates discarded information.

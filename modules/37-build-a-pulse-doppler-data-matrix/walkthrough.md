# P37 walkthrough: Trace a Target Across Two Time Axes

## Guiding question

What are fast time and slow time in a radar data block?

Run `experiment.m` once with the visible controls unchanged. Inspect one plot
or processing transition at a time.

## Baseline observation

The baseline uses 256 fast-time samples at 20 MHz and 32 pulses at a 5 kHz
PRF. The matrix is therefore `256 x 32`: rows are delay/range samples and
columns are coherent pulse looks.

1. In `P37 selected fast-time pulse columns`, find the three range peaks in
   several pulse columns. They stay near rows 61, 121, and 161, corresponding
   to measured ranges near 449.7, 899.4, and 1199.2 m.
2. In `P37 selected slow-time range rows`, follow each target row across pulse
   index. The stationary target has nearly flat phase; the `+12 m/s` target has
   a positive slope; the `-18 m/s` target has a negative slope.
3. In `P37 pulse-Doppler data matrix`, read vertical position as fast-time
   range and horizontal position as slow-time pulse index. The magnitude view
   shows the rows clearly but does not make velocity sign obvious.
4. Read `results`. Range-bin spacing is about `7.495 m`, PRI is `200 us`, and
   the moving-target Dopplers are about `+800.6 Hz` and `-1200.8 Hz`.

Expected observation: delay fixes where a target appears down each column;
velocity controls how its complex sample rotates from column to column.
The fastest target moves only about `0.112 m` during the sampled dwell, or
`0.015` of a range bin, which makes the fixed-row approximation visible and
bounded rather than implicit.

## Sweep one variable: target range

Inspect `P37 range-to-row sweep`. The script changes only target range among
300, 750, and 1200 m. Each range response moves to a different fast-time row.
The pulse count, PRF, carrier, amplitude, and velocity law are unchanged.

Prediction to check: increasing target range by one range-bin spacing should
move the ideal center by one row. The reported range may differ from truth by
up to half a bin because delay is sampled.

## Sweep one variable: target velocity

Inspect `P37 velocity-to-column-phase sweep`. All three sequences represent
the same range row and unit magnitude, but velocities `-18`, `0`, and
`+18 m/s` create negative, zero, and positive phase slopes across columns.

Expected observation: velocity changes the slow-time sinusoid without moving
the target to another fast-time row. Reversing velocity reverses phase slope;
it does not reverse range.

## Intentionally broken case

Move to `P37 phase-loss failure and recovery`. The broken chain applies
`abs(data_matrix)` before extracting the `+12 m/s` target row.

1. The range peak is still present because echo strength survived.
2. The magnitude-only row has zero adjacent phase increment.
3. Its slow-time spectrum is driven to the zero-Doppler bin.

Failure interpretation: the target did not become stationary. Magnitude-only
processing erased the pulse-to-pulse angle that carried signed motion. A
magnitude matrix is useful for seeing range energy, but it is not the complete
coherent radar measurement.

## Recovery

Restore the complex data matrix with fast-time rows and pulse columns. The
script creates a second private `RandStream` with seed 3701, regenerates the
same complex noise, and asserts exact equality with the baseline matrix. The
recovered adjacent phase increment must match the baseline target row.

If a run is interrupted, use Ctrl+C and rerun the script. Every loop, matrix,
and figure group has an explicit bound; there is no worker, timer, network
request, hardware session, file write, or external transaction to cancel or
roll back. Only figures tagged `P37` are closed. Private streams do not alter
the global random stream, and the script never reads or writes `.learning/`.

## Concept connection and completion handoff

P35 mapped receive delay into one fast-time interval. P36 treated one selected
range bin as a slow-time complex tone. P37 places all range bins into rows and
all pulse looks into columns. P38 will subtract columns to suppress stationary
returns, while P42 will transform every row across slow time into Doppler.

Batch rollback removes the four P37 implementation artifacts, focused test,
and P37 evidence; restores this README and P37 manifest status to
`scaffolded`; and restores the public catalogs. It preserves P01-P36 and every
later module identity.

Completion means you can trace one target through raw data to its range bin and slow-time sinusoid.

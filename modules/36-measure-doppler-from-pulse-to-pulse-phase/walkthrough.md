# P36 walkthrough: Follow the Slow-Time Rotation

## Guiding question

How does target velocity create coherent phase progression across pulses?

Run `experiment.m` once without changing the visible controls. Work through
one figure or processing transition at a time.

## Baseline observation

The baseline uses a 10 GHz carrier, 4 kHz PRF, 32 coherent pulses, and a
`+15 m/s` approaching target. Before changing anything:

1. In `P36 slow-time complex echo`, follow I and Q versus pulse index, then
   follow the connected points around the complex plane. Positive velocity
   rotates counterclockwise under this module's sign convention.
2. In `P36 phase slope and Doppler FFT`, compare the noisy unwrapped phase with
   the straight ideal line. The slope is phase accumulated per unit slow time.
3. Read the FFT peak and `results`. The ideal Doppler is about `1000.69 Hz`,
   the phase step is about `1.572 rad/pulse`, and the 32-pulse FFT grid is
   `125 Hz` per bin. The phase estimate can be continuous while the FFT peak
   is constrained to its grid.

Expected observation: the I/Q rotation, positive unwrapped-phase slope,
positive Doppler peak, and positive velocity estimate all tell the same story.

## Sweep one variable: signed velocity

Keep carrier, PRF, pulse count, and amplitude fixed. Inspect
`P36 velocity and direction sweep` for `-20, -10, 0, +10, +20 m/s`.

- Receding negative velocities produce negative Doppler and phase steps.
- Zero velocity produces zero phase step.
- Approaching positive velocities produce positive values.

Prediction to check: changing `+15` to `-15 m/s` should reverse the I/Q
rotation and phase slope without changing the ideal echo magnitude.

## Sweep one variable: carrier frequency

Keep the physical target at `+15 m/s` and PRF at 4 kHz. Compare 5, 10, and
15 GHz in `P36 carrier-frequency sweep`.

Expected observation: doubling carrier frequency doubles Doppler and phase
step because wavelength halves. At the same time, the unambiguous speed
magnitude falls. Carrier frequency changes the measurement sensitivity, not
the target's true velocity.

## Sweep one variable: coherent pulse count

Keep carrier, PRF, and target velocity fixed. Compare 8, 16, 32, and 64 pulses
in `P36 pulse-count sweep`.

Expected observation: `PRF/N` falls from 500 to 62.5 Hz and the corresponding
velocity-bin spacing narrows. The unambiguous Doppler interval stays
`[-2000, 2000) Hz` because PRF did not change. Do not interpret a narrower
bin as guaranteed accuracy under acceleration or loss of coherence.

## Intentionally broken case

Move to `P36 coherence failure and recovery`. The broken chain uses
`abs(received_echo)` before adjacent-phase and FFT processing.

1. The magnitude-only spectrum is dominated by zero Doppler.
2. Its adjacent phase increment is zero because the samples are real and
   nonnegative.
3. The report cannot retain the sign or rate of the target's phase rotation.

Failure interpretation: the target did not stop. The processor discarded the
complex phase observable. Magnitude can support noncoherent detection, but it
cannot recover signed pulse-to-pulse Doppler for this constant-amplitude echo.

## Recovery

Restore the coherent complex range-bin samples. The script creates a second
private `RandStream` with seed 3601, reconstructs the noise, and asserts that
the recovered samples exactly equal the baseline. The recovered adjacent-
phase velocity must therefore equal the baseline estimate.

If a run is interrupted, use Ctrl+C and rerun from a clean workspace. Every
loop and array is bounded; there is no worker, timer, network request,
hardware session, file write, or external transaction to cancel or roll back.
Only figures tagged `P36` are closed. The private stream does not alter the
global random stream, and the script never reads or writes `.learning/`.

## Concept connection and completion handoff

P35 limited unique fast time to one PRI and created range aliases. Here the
same PRF samples slow-time phase and creates Doppler aliases. P37 will place
many range bins beside these pulse samples to form a pulse-Doppler matrix.

Batch rollback removes the four P36 implementation artifacts, focused test,
and P36 evidence; restores this README and P36 manifest status to
`scaffolded`; and restores the public catalogs. It preserves P01-P35 and every
later module identity.

Completion means you can predict phase increment per pulse and velocity from the Doppler-bin location.

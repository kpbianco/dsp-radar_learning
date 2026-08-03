# Walkthrough

## Guiding question

Why can an estimate be precise even when two targets cannot be resolved?

## Baseline observation

Run `experiment.m` without changing the visible controls. Start with Figure 1.
The upper plot is the finite Gaussian-envelope pulse. The lower plot is the
matched response from two targets separated by 22 m at 4 MHz bandwidth and high
SNR.

Observe the true-range markers and count physical local maxima. The pair makes
one blended maximum even though the display contains many range samples. Record
the nominal `c/(2B)` scale and the measured full −3 dB response width; they are
related scales, not guaranteed to be identical.

## Sweep one variable: bandwidth only

Move to Figure 2. `bandwidth_sweep_hz = [2e6 4e6 8e6]`; target ranges, sample
rate, amplitude, noise realization, and high matched-filter SNR stay fixed.

As bandwidth rises, the time pulse shortens and the measured response width
falls. The 22 m pair progresses from a blended response to two visible maxima.
Explain the change physically: a narrower correlation footprint causes less
overlap between the two delayed copies.

## Sweep one variable: target spacing only

Figure 3 keeps the 4 MHz waveform and high SNR fixed while
`separation_sweep_m = [10 22 45]` changes. The first two responses merge; the
wide pair produces two maxima. This sweep prevents a common causal mistake:
bandwidth did not change here—the scene geometry did.

## Hold bandwidth fixed: estimate one target

Figure 4 removes the second target and keeps the 4 MHz waveform. Compare the
integer-bin estimate with the parabolically refined estimate. The relevant
quantity is absolute error from the known single-target range, not the width of
the pulse response.

Figure 5 then changes only matched-filter SNR over `[0 15 30]` dB across the
same seeded trial bank. Read bias, standard deviation, and RMSE separately.
The RMSE and repeatability improve with SNR while the clean matched-response
width remains fixed. Check that the high-SNR RMSE is smaller than that width;
this is accurate single-target ranging, not proof of two-target resolution.

## Intentionally broken case

In Figure 6 the unresolved 4 MHz pair is linearly interpolated onto a grid 16
times denser. The broken rule selects the two largest display samples and calls
them two targets. They sit beside each other on one crest, even though the true
targets are 22 m apart and the original response has only one physical maximum.

Stop here and state the failure: display spacing was mistaken for waveform
resolution, and a one-peak mixture was forced into a two-target report.

## Recover and connect the concept

The recovery restores the local-maximum criterion and labels the 4 MHz pair
unresolved. It then changes a physical information-bearing parameter—bandwidth
to 8 MHz—and recovers two maxima. Resetting the private seed reproduces the
baseline noise and matched response exactly; no hidden external state is needed.

Use Ctrl+C if the bounded Monte Carlo loop must be cancelled. Rerunning begins
from validated controls and a fresh private seed. The script closes only figures
tagged `P31`; it does not touch the global random stream, `.learning/`, files,
workers, timers, hardware, network services, or external transactions.

For rollback, remove the four implementation artifacts, restore this module's
README to its scaffolded brief, set only P31's manifest status back to
`scaffolded`, and revert the P31 catalog/test/evidence entries. Learner progress
under ignored `.learning/` is separate and must not be committed or rewritten.

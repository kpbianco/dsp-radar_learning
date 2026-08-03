# P42 walkthrough: Create a Full Range-Doppler Map

Guiding question: **How do matched filtering and slow-time FFT combine to separate targets?**

Run `experiment.m` section by section. Keep `target_ranges_m` and
`target_velocities_mps` visible, but observe one processing transition before
reading every metric.

## Baseline: follow the two dimensions

Run through **Final range-Doppler map**.

1. In Figure 1, identify the long raw echoes. Do not try to read precise target
   range from their leading and trailing interference pattern.
2. In Figure 2, compare raw pulse 1 with its compressed response. Then inspect
   the lower image: matched filtering sharpens rows without removing the pulse
   columns.
3. In Figure 3, look only at the row near 1.2 km. Find two velocity peaks. That
   row contains targets 1 and 2 at one range but with different phase slopes.
4. In Figure 4, match the three white truth markers to bright neighborhoods.
   Targets 2 and 3 share velocity but occupy different range rows.

Expected observation: the three targets become separate 2-D neighborhoods
only after both stages. Stationary clutter accumulates near zero velocity;
noise remains spread.

Common mistake: calling the finest plotted range increment the range
resolution. Read `results.range_sample_spacing_m` and
`results.nominal_range_resolution_m`; the latter is set by bandwidth.

## Sweep 1: change only CPI length

Run **Sweep 1** with `cpi_pulse_sweep = [16 32 64]`.

- Waveform bandwidth, sample rate, PRF, scene, and Hann window family stay
  fixed.
- Compare the printed velocity-bin spacing in each subplot.
- Watch the two shared-range Doppler responses become more distinguishable as
  the coherent observation grows.

Expected observation: doubling pulse count halves `PRF/N` and the velocity-bin
spacing. Range resolution does not change.

Now try `[16 40 64]`, rerun from control validation, and confirm the monotonic
trend. Restore `[16 32 64]` afterward so the retained baseline is
deterministic.

Common mistake: attributing the narrower Doppler response to more zero-padding.
Each case actually uses more measured pulses and therefore a longer CPI.

## Sweep 2: change only the slow-time window

Run **Sweep 2**. The same fractional-bin coherent tone is processed with a
rectangular window and a Hann window. Both spectra are divided by their window
sums.

Expected observation: the Hann curve has lower energy outside the guarded
mainlobe neighborhood, but its central response occupies at least as many
-6 dB bins. Lower sidelobes and narrower mainlobe are competing goals.

For a second one-variable look, change `window_tone_offset_bins` from `10.10`
to `10.35`. The leakage pattern moves because the tone is farther from a bin;
neither window changes its physical tone frequency. Restore `10.10`.

Common mistake: comparing unnormalized window peaks and concluding the Hann
window weakened the simulated target. Its weight sum, mainlobe width, and
sidelobes all matter.

## Intentionally broken case: use the wrong matrix dimension

Run **Intentionally broken case**.

Expected observation: the left panel is finite and structured, but its axes
are normalized fast-time frequency and pulse index. It has neither an aligned
range coordinate nor a Doppler coordinate. It is not a range-Doppler map.

Explain the failure in physical terms: the code transformed dimension 1 after
dimension 1 had already been assigned to range. It never transformed the
complex pulse history in dimension 2, so it never measured Doppler.

Common mistake: accepting a colorful matrix because it has the expected array
size. Shape is not axis semantics.

## Recovery

Run **Recovery**. The right panel restores multiplication by the Hann weights
across columns and performs the FFT along dimension 2. Confirm:

- `results.broken_model_valid` is false;
- `results.recovered_model_valid` is true;
- `results.recovery_error` is at roundoff scale;
- every target is again within the stated range and velocity tolerance.

The recovery reuses the already compressed deterministic data. A full clean
rerun also reconstructs clutter and noise from private seed `4201`.

## Concept connection

Complete this sentence aloud:

> Matched filtering separates delay along ___, while the slow-time FFT
> separates coherent phase rate along ___; bandwidth controls ___ and CPI
> duration controls ___.

The intended connection is fast time/range, slow time/velocity, range
resolution, and Doppler spacing. This map becomes data for detection lessons;
it is not itself a detector.

## Interruption, recovery, and rollback

`Ctrl+C` may leave partial figures or workspace arrays but cannot leave an
external transaction: the script has no file, network, worker, timer, or
hardware output. Rerun from the top to clear only figures tagged `P42`, reset
workspace variables, and recreate the private-seed scene within bounded
resource ceilings.

Repository rollback is file-local: remove the P42 learning artifacts and
focused evidence/catalog changes, then restore only P42's manifest status to
`scaffolded`. Preserve P41, later module identities, ignored `.learning/`
progress, and the operator-managed active-batch contract.

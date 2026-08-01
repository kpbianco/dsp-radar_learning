# P11 Walkthrough: Make FFT Bins Concrete

## Guiding question

What frequency does each FFT bin represent?

Run `experiment.m` once from its module directory. It is finite and
noninteractive. A rerun replaces only figures tagged `P11`, uses the same
private seed, writes no files, and does not reset MATLAB's global random stream.

## Baseline: read the bin before reading the peak

The visible controls are \(f_s=1024\) samples/s, \(N=64\), and zero-based
`tone_bin = 9`. Calculate \(\Delta f=1024/64=16\) Hz, then calculate
\(f_9=9(16)=144\) Hz.

Open **P11 baseline bin map**.

1. In the time view, notice that I and Q are the two coordinates of one
   rotating complex tone, not two unrelated signals.
2. In the bin-number view, locate zero-based bin 9.
3. In the centered view, confirm that the same projection is at +144 Hz.
4. In the phase view, note that low-magnitude bins are intentionally hidden.

Expected observation: the explicit DFT and `fft` agree to the script's tight
tolerance. The largest normalized projection is near 1 V at bin 9, stored at
MATLAB index 10. The small seeded noise perturbs the ideal value slightly.

## Sweep 1: change only fractional-bin offset

Open **P11 fractional-bin sweep**. The script reuses the same samples, sample
rate, record length, amplitude, phase, and exact noise realization. Only the
offset changes through 0, 0.25, and 0.50 bin.

- At 0 bin offset, one projection dominates.
- At 0.25 bin, the nearest bin is still largest, but neighboring projections
  become visible.
- At 0.50 bin, bins 9 and 10 have nearly equal magnitude (about \(2/\pi\), or
  0.637 V, for the ideal unit complex tone).

Inspect `results.offset_lower_phase_rad` and
`results.offset_upper_phase_rad`. At half-bin their wrapped difference is near
\(\pi\). Do not compare the phase of small distant bins: their magnitude does
not support a stable phase interpretation.

## Sweep 2: change only record length

Open **P11 record-length sweep**. The physical tone stays fixed at 144 Hz and
the sample rate stays at 1024 samples/s. Only \(N\) changes.

| N (samples) | Duration (ms) | Bin spacing (Hz) | Tone location (bins) |
| ---: | ---: | ---: | ---: |
| 32 | 31.25 | 32 | 4.5 |
| 64 | 62.5 | 16 | 9 |
| 128 | 125 | 8 | 18 |

Expected observation: the 32-sample record spreads because 144 Hz falls
halfway between two projections. The 64- and 128-sample records are coherent,
but the peak bin number changes because the frequency grid changed. Longer
duration produces smaller spacing; it did not move the tone.

## Broken case

Open **P11 broken axis and recovery**. The top panel uses
`(1:N)*delta_f`, silently treating MATLAB array indices as zero-based bins.
The spectrum samples are correct, but the labels report the 144 Hz tone as
160 Hz—exactly one 16 Hz bin high.

This is an intentionally broken metadata path. In a radar chain, the identical
mistake would bias every bin-to-range or bin-to-Doppler conversion even though
the FFT values themselves are correct.

## Recovery and rollback

The bottom panel uses `(0:N-1)*delta_f`, or equivalently
`k = MATLAB index - 1`. It reports 144 Hz and leaves zero frequency at array
index 1.

If execution takes unexpectedly long, press Ctrl+C. Reduce nothing below the
teaching contract; first restore the fixed resource ceilings and visible
controls, then rerun. Because the script writes no files and replaces only P11
figures after all calculations and assertions pass, cancellation leaves no
persistent partial result. Rerunning with the private seed recovers the same
noise realization.

Repository rollback is similarly isolated: remove P11-owned artifacts and
restore only its manifest status to `scaffolded`; preserve P10, later module
identity, and personal `.learning/` state.

## Concept connection

For a radar Doppler FFT, replace hertz with \(v=\lambda f_d/2\) after the bin
frequency is correct. For a sampled beat frequency or range FFT, apply the
waveform's frequency-to-range scale after the same mapping. The physical units
come after the DFT grid; an off-by-one bin at this stage becomes a systematic
physical bias.

Continue to `checks.md` when you can separate these three numbers without
mixing them: MATLAB index, zero-based bin, and frequency in hertz.

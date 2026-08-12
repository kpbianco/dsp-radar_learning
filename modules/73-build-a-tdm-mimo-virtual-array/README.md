# P73: Build a TDM-MIMO Virtual Array

**Phase 8: FMCW, MIMO, and Micro-Doppler**  
**Status:** Implemented by governed batch `P73`

## Guiding question

How do multiple transmit and receive channels create more spatial samples?

## Experiment

Build a two-transmit, four-receive TDM-MIMO radar explicitly. The physical
positions combine as `x_virtual = x_tx + x_rx`, producing eight contiguous
half-wavelength virtual positions from only four simultaneous receive
channels. Form every conventional scan weight directly and compare the
receive-only and virtual-array beam patterns and angle estimates.

## Procedure

Inspect the physical and virtual geometry, then compare receive-only and
virtual half-power beamwidth. Sweep the separation of two equal incoherent
targets while holding the array and scene center fixed. Next sweep target
velocity while holding geometry and angle fixed. In the broken moving-target
case, ignore the delay between TX slots, observe the biased angle, estimate
Doppler from repeated same-TX looks, and compensate the unchanged TDM record.

## What this should teach

For broadside-referenced angle `theta`, the channel at TX position `x_p` and
RX position `x_q` has spatial phase

```text
exp(-j 2 pi (x_p + x_q) sin(theta) / lambda).
```

The TX/RX position sums act like additional sensor locations, so the reviewed
`2 x 4` geometry doubles the spatial samples and increases aperture from
`1.5 lambda` to `3.5 lambda`. The minus sign is the P69-P72
`tx .* conj(rx)` dechirped convention; P61's raw receive snapshot has the
opposite spatial sign. Because TDM channels are not simultaneous, a
moving target also contributes `exp(-j 2 pi f_d t_p)`. If that temporal phase
is treated as geometry, the angle scan is biased; same-TX slow-time Doppler
provides the correction used here.

## Completion condition

You can draw the physical and virtual geometry, explain why the virtual array
has a narrower beam and separates a closer pair, and show how inter-TX motion
phase biases then recovers the angle on unchanged data.

## Run the lesson

```bash
./bin/learn start 73
```

In MATLAB, run `experiment`, follow `walkthrough.md` one observation at a time,
and use `checks.md` before giving the short teach-back.

## Dependencies and compatibility

P61 supplies the broadside angle and positive spatial-phase convention, P62
connects aperture with beamwidth, P63 supplies the explicit Hermitian
conventional scan, P70 supplies slow-time Doppler phase, and P72 is the
governed batch prerequisite.

The script requires MATLAB R2016b or newer and no optional toolbox. It uses
explicit position sums, complex exponentials, Hermitian coherent sums, a
lag-one same-TX Doppler estimate, and a private deterministic noise generator.
It is bounded to 32 virtual channels, 128 TDM cycles, 2,001 scan angles, seven
cases per sweep, 20,000 private-generator values per request, 500,000 retained
numeric values, and five tagged figure groups. It writes no file and starts no
network request, timer, worker, or external process.

This is an ideal narrowband, far-field, calibrated, colocated TDM model. It
uses a stop-and-hop constant-angle/constant-velocity target and omits FMCW
fast-time range processing, range migration, acceleration, multipath, mutual
coupling, channel mismatch, phase noise, TX leakage, ADC effects, detection,
and calibrated power. Static checks and a standard-library numerical oracle
do not constitute MATLAB runtime, rendered-figure, RF, antenna, bench,
hardware/HIL, real-time, field, or operational-radar validation.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Build a TDM-MIMO Virtual Array". The guiding question is: "How do multiple transmit and receive channels create more spatial samples?" Use this experiment: Simulate a small TDM-MIMO FMCW radar, construct the virtual-element positions, and estimate target angle. Have me perform these actions: Compare physical RX-only and virtual-array beam patterns. Add target motion between transmit slots and observe angle/Doppler phase error. The main concept I must learn is: MIMO synthesizes a larger aperture from TX-RX position sums, but TDM timing couples target motion into virtual-array phase. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files

- `README.md`
- `experiment.m`
- `lesson.md`
- `walkthrough.md`
- `checks.md`

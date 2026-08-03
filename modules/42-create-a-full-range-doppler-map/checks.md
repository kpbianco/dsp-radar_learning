# P42 checks: Create a Full Range-Doppler Map

Guiding question: **How do matched filtering and slow-time FFT combine to separate targets?**

Use Figures 2–7 and the `results` structure. These checks ask for physical
interpretation, not MATLAB syntax recall.

## Observation checks

1. Which plot first gives narrow target range neighborhoods?
2. At approximately 1.2 km, why are there two velocity peaks?
3. Which two targets share velocity, and what separates them on the map?
4. Where does the stationary clutter concentrate in velocity?
5. How do range sample spacing and nominal range resolution differ?
6. As CPI pulse count rises from 16 to 64, what happens to velocity-bin
   spacing?
7. Relative to rectangular weighting, what two visible changes does the Hann
   window make?
8. What coordinates label the broken left panel in Figure 7?

## Interpretation checks

1. Explain why range compression acts independently on every pulse column.
2. Explain why the Doppler FFT must act across columns after range compression.
3. Why does the matched-filter output require removal of a fixed filter delay
   before a range axis is assigned?
4. Why can two targets share a range cell yet remain separable?
5. Why does a longer CPI improve Doppler spacing without changing waveform
   range resolution?
6. Why must coherent gain be normalized before comparing window peaks?
7. Why is `fft(range_compressed,[],1)` not a range-Doppler transform?
8. Why is a bright cell not automatically a detection or target report?

## Prediction checks

1. If waveform bandwidth doubles while sample rate and CPI stay fixed, what
   happens to nominal range resolution and Doppler-bin spacing?
2. If PRF doubles with pulse count fixed, what happens to unambiguous velocity
   and Doppler-bin spacing?
3. If pulse count doubles at fixed PRF, what happens to approximate CPI
   duration and velocity-bin spacing?
4. If a target velocity becomes zero, where does it appear relative to
   stationary clutter?
5. If complex range-compressed samples are replaced by magnitudes before the
   slow-time FFT, what signed-motion information is lost?
6. In the ideal noiseless case, what happens to rectangular-window leakage
   when target Doppler falls exactly on an FFT bin?

## Completion checklist

- [ ] I can state the fast-time rows by slow-time columns convention.
- [ ] I can explain `R = c*tau/2` and `f_d = 2v/lambda` from the visible axes.
- [ ] I can find all three truth markers within the stated resolution/bin
      tolerance.
- [ ] I can distinguish range sample spacing from waveform range resolution.
- [ ] I can connect CPI duration to Doppler spacing without invoking
      zero-padding.
- [ ] I can describe the Hann sidelobe/mainlobe tradeoff after coherent-gain
      normalization.
- [ ] I can reject the wrong-axis FFT even when its matrix looks plausible.
- [ ] I can explain the private-seed clean rerun and P42-only rollback boundary.

## Answer key

1. Figure 2, after the conjugate time-reversed waveform is correlated with
   each pulse.
2. Targets 1 and 2 share approximately 1.2 km but have different coherent
   phase rates, so the slow-time FFT separates them.
3. Targets 2 and 3 share velocity; their different echo delays place them in
   different matched-filter range rows.
4. Near zero radial velocity because its coefficient is held constant across
   pulses in this idealized scene.
5. `c/(2Fs)` is coordinate sampling; approximately `c/(2B)` is matched-response
   width and physical range scale.
6. It falls in inverse proportion to pulse count.
7. Sidelobes fall and the mainlobe widens; coherent gain is separately
   normalized.
8. Normalized fast-time frequency and pulse index, not range and velocity.
9. Each target delay is encoded inside one received pulse, so correlation is
   performed down one column at a time.
10. Doppler is pulse-to-pulse phase rate at a fixed range, so the transform
    runs across columns.
11. Convolution peaks include `Ns-1` samples of matched-filter delay; failing
    to remove it biases every range label.
12. They occupy one range neighborhood but different Doppler bins.
13. More coherent pulses extend slow-time observation; waveform and bandwidth
    remain unchanged.
14. Otherwise the smaller Hann weight sum looks like physical target loss.
15. Dimension 1 is the range/fast-time dimension. Its FFT produces fast-time
    frequency and leaves pulse index untransformed.
16. Clutter, sidelobes, and noise also produce bright cells; detection requires
    an explicit threshold/statistical rule.
17. Nominal range resolution halves; Doppler-bin spacing is unchanged.
18. Unambiguous velocity and bin spacing both double, while CPI duration
    halves.
19. CPI duration doubles and velocity-bin spacing halves.
20. At zero Doppler, potentially overlapping stationary clutter.
21. Pulse-to-pulse phase direction and therefore Doppler sign.
22. Its energy falls into one bin, so ideal rectangular-window leakage
    vanishes at the sampled FFT frequencies.

## Short teach-back rubric

A complete teach-back should say, in about one minute:

- fast-time matched filtering converts known-waveform delay into range while
  preserving coherent pulse history;
- a windowed FFT across slow time converts that history's phase rate into
  signed radial velocity;
- bandwidth governs range response width, while CPI and slow-time window
  govern Doppler spacing and sidelobe/mainlobe tradeoffs;
- a matrix is a valid range-Doppler map only when operations and axis units
  match those two dimensions, and the resulting energy is not yet a detector.

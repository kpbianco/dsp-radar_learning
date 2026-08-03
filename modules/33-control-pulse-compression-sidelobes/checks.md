# P33 checks: Control Pulse-Compression Sidelobes

Guiding question: **Why can a strong target hide a weak nearby target after matched filtering?**

Use the figures and printed metrics. These are interpretation checks, not a
MATLAB syntax quiz.

## Observation checks

1. Which isolated response has lower PSLR: rectangular or Hann-like?
2. Which response has the larger full -3 dB range width?
3. At the 17-sample separation, which filter changes the clean weak/leakage
   margin from negative to positive?

Passing observation: you identify the Hann-like response's lower sidelobes,
wider mainlobe, and positive baseline visibility margin.

## Prediction checks

1. As `alpha` moves from 0 toward 1, predict the directions of PSLR, mainlobe
   width, and output-SNR change before reading Figure 3.
2. If the weak target moves inside the tapered mainlobe, predict whether lower
   far sidelobes alone will separate it.
3. If a scalar doubles both tapered signal and tapered noise amplitude, predict
   whether output SNR changes.

Passing prediction: stronger taper lowers PSLR, widens the response, and costs
SNR; close targets remain merged; scalar normalization does not restore SNR.

## Interpretation checks

1. Explain why a strong target contributes energy at the weak target's range.
2. Distinguish peak-amplitude loss from output-SNR loss for the Hann-like
   filter.
3. Explain why each response is normalized to its own peak in Figure 1 but the
   script still prints a separate SNR metric.
4. Explain why a positive isolated leakage margin is useful but is not a
   probability-of-detection claim.

Passing interpretation: you connect the finite LFM response to deterministic
sidelobes, use `20*log10` for magnitude and `10*log10` for SNR, and retain the
noise/phase/detection limitations.

## Failure and recovery checks

1. Why does the lowest-PSLR rule fail at seven samples of separation?
2. Is the broad feature in Figure 5 proof that only one target exists?
3. What scene change does the scripted recovery restore, and what exact state
   is recreated?

Passing recovery: you identify widened-mainlobe overlap, reject absence as an
unsupported conclusion, restore 17 samples of separation, and recreate the
private seed and exact Hann-like response. If needed, cancel with Ctrl+C; there
is no worker, timer, external transaction, or persistent resource to clean up,
and only figures tagged `P33` are closed.

## Completion checklist

- [ ] I can explain how strong-target sidelobes mask a weak echo.
- [ ] I can compare PSLR, -3 dB width, and visibility margin without treating
      them as the same metric.
- [ ] I can distinguish the roughly 6 dB raw Hann-like peak change from the
      roughly 1.77 dB output-SNR loss.
- [ ] I can predict when a wider tapered mainlobe becomes the limiting factor.
- [ ] I can choose between rectangular and tapered processing for a stated
      separation/dynamic-range objective.
- [ ] I know this base MATLAB simulation is not hardware, field, real-time, or
      operational-radar validation.

## Short teach-back rubric

Give two or three sentences that include all three ideas:

1. A finite LFM pulse gives every strong point target a mainlobe and sidelobes,
   so a weak neighbor can sit under deterministic leakage.
2. Receive tapering lowers sidelobes but widens the mainlobe and loses some
   output SNR.
3. Weighting should be selected using target separation and required dynamic
   range, not PSLR alone.

Completion means you can select weighting that reveals the weak target and quantify the resolution/SNR cost. Personal completion is recorded only after this teach-back through the learner CLI under ignored `.learning/` state.

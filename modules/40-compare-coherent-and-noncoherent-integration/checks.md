# Checks: coherent and noncoherent integration

Guiding question: When should pulse phases be added and when should magnitudes be added?

Use the four figure groups and console metrics. Explain the signal behavior rather than MATLAB syntax.

## Observation checks

1. In the baseline, what changes between the raw I/Q panel and the phase-aligned I/Q panel?
2. For 32 stable-phase pulses, what coherent output SNR does the console report from a -8 dB single-pulse input?
3. In the broken case, which statistic loses its target evidence and which remains unchanged?

## Interpretation checks

4. Why must coherent processing multiply by a conjugate phase reference before summing?
5. Why does stable coherent output SNR grow as `N*rho`?
6. Why does P40 compare coherent and noncoherent statistics using detectability `d` instead of calling both raw statistic values “output SNR”?
7. Does a positive noncoherent power sum prove a target is present?
8. What does the Gaussian phase-jitter factor `exp(-sigma_phi^2)` represent physically?

## Prediction checks

9. If pulse count increases from 16 to 64 with stable phase, predict the coherent SNR change in decibels.
10. If the phase-jitter standard deviation becomes very large, predict the coherent gain relative to one pulse and the normalized noncoherent target energy.
11. If all pulses have the same unknown but constant phase offset, will coherent gain be lost when only magnitude of the final sum matters?
12. If a pulse-by-pulse phase tracker estimates the residual errors exactly, predict the broken-case coherent signal-power fraction after derotation.

## Answers and evidence

1. The predicted target rotation is removed. The clean target contribution would align along positive I; noise still spreads in I and Q.
2. About 7.05 dB: `-8+10 log10(32)`.
3. The nominal-reference coherent sum cancels to zero. The phase-insensitive target energy remains normalized to one.
4. Complex arrows must share a reference direction before addition. Otherwise their target components can oppose and cancel.
5. Target amplitude grows by `N`, so target power grows by `N^2`; independent noise power grows by `N`. Their ratio therefore gains `N`.
6. The coherent power and summed-power statistics have different noise-only distributions. Detectability `d` divides each target-induced mean shift by its own noise-only standard deviation, providing a common separation measure.
7. No. Noise power is positive and accumulates even with no target; a threshold tied to a false-alarm model is required.
8. It is the retained cross-pulse coherence. Increasing jitter randomizes relative directions and suppresses the target cross-terms in the complex sum.
9. The pulse count grows by four, so coherent SNR increases by `10 log10(4)=6.02` dB.
10. Coherent gain approaches one pulse, while normalized noncoherent target energy stays at one in this constant-amplitude model.
11. No. A common constant offset rotates the final coherent sum but does not reduce its magnitude; pulse-to-pulse phase variation causes cancellation.
12. It returns to one, the ideal normalized signal-power fraction.

## Short teach-back rubric

A complete teach-back should state all four ideas in about a minute:

- coherent integration preserves I/Q and aligns a defensible pulse phase before adding;
- stable phase gives `N` output-SNR gain because signal adds in amplitude while noise adds in power;
- noncoherent power integration discards phase, tolerates unknown pulse directions, and separates target from noise less efficiently;
- untracked phase variation can erase coherent benefit, while accurate derotation or an honest noncoherent statistic provides recovery.

Before personal completion, use Figures 2 through 4 to identify one efficient coherent case, one phase-uncertain case, and the recovery operation.

# P33 lesson: Control Pulse-Compression Sidelobes

Guiding question: **Why can a strong target hide a weak nearby target after matched filtering?**

## Physical model: every compressed peak has a skirt

P32 showed that the conjugate time-reversed LFM pulse concentrates a long echo
into a narrow delay peak. The concentration is not perfect. A finite pulse has
a mainlobe surrounded by sidelobes, so a unit point target produces a complete
range response rather than one nonzero range cell.

For a strong target at delay `k_s` and a weak target at `k_w`, linearity
gives

\[
y[k]=A_s r[k-k_s]+A_w r[k-k_w]+v[k],
\]

where `r[k]` is the pulse-compression response and `v[k]` is filtered
noise. At the weak target's range, the desired contribution competes with the
strong target's sidelobe. A weak echo can therefore be present in the samples
without forming a visible second peak.

The baseline uses `A_s = 1`, `A_w = 0.04`, an amplitude ratio of about
-28 dB, and 17 range samples (about 63.7 m) of separation. The rectangular
LFM response places enough strong-target leakage at that offset to exceed the
weak target's coherent peak.

## Receive weighting reshapes the range response

For transmit samples `s[n]`, the rectangular matched filter is

\[
h[n]=s^*[N-1-n].
\]

P33 constructs a Hann-like cosine explicitly,

\[
w[n]=\tfrac12-\tfrac12\cos\left(\frac{2\pi n}{N-1}\right),
\]

and uses the tapered replica

\[
h_w[n]=(s[n]w[n])^*\big|_{n\rightarrow N-1-n}.
\]

This is a deliberate mismatched receive filter because the transmitted pulse
still has a rectangular amplitude gate. Samples near the pulse endpoints now
contribute less. Their cancellation away from the correct delay improves, so
peak sidelobes fall, but fewer samples contribute equally to the focused peak.
Figure 1 shows the resulting lower sidelobes and wider mainlobe.

The experiment measures peak sidelobe ratio (PSLR) outside the first local
minimum on each side of the mainlobe. It does not use a fixed exclusion width,
because the taper itself changes that width.

## Visibility margin separates masking from noise luck

The clean, isolated strong-target response is evaluated at the weak target's
delay. For weights `w[n]`, the aligned weak-target contribution has magnitude

\[
P_w=|A_w|\sum_n w[n].
\]

The reported visibility margin is

\[
M=20\log_{10}\left(\frac{P_w}{L_s(k_w)}\right),
\]

where `L_s(k_w)` is the magnitude of the isolated strong-target leakage at
that range. Negative margin means sidelobe leakage is larger than the weak
target's coherent contribution; positive margin means weighting has relieved
that particular masking mechanism. This metric is deliberately computed from
clean isolated components, while seeded noise is shown in the profiles. It is
not a probability of detection and it does not remove target-phase
interference.

## The cost has two different dB labels

The unnormalized Hann-like peak is about 6 dB below the rectangular peak
because its weights sum to about `N/2`. That is a **peak-amplitude change**.
A scalar gain can restore the plotted peak height, but it scales noise too.

For white input noise, signal amplitude at the correct delay is proportional
to `sum(w)`, while output noise power is proportional to `sum(w.^2)`. The
output-SNR change relative to the rectangular matched
filter is therefore

\[
L_{SNR}=10\log_{10}
\left(\frac{(\sum_n w[n])^2}{N\sum_n w^2[n]}\right).
\]

For this sampled Hann-like taper it is about -1.77 dB, not -6 dB.
Normalization cannot erase this SNR loss. The full -3 dB width also grows from
about 16.4 m to 26.9 m. Sidelobe suppression has bought dynamic range by
spending SNR and close-target resolution.

## Two one-variable views of the trade

Figure 3 moves only the cosine strength

\[
w_\alpha[n]=(1-\alpha)+\alpha w[n]
\]

through `alpha = [0 0.5 1]`. The waveform, scene, noise record, and target
separation remain fixed. Increasing `alpha` lowers PSLR, widens the -3 dB
mainlobe, increases SNR loss, and eventually makes the baseline weak-target
margin positive.

Figure 4 moves only the weak target through offsets `[7 13 17 32]` samples.
The target amplitude, waveform, and filters remain fixed. A taper is not
uniformly superior at every range: its leakage follows a different ripple
pattern, and its wider mainlobe makes very close targets harder to separate.

## The broken lowest-sidelobe rule

The deliberately broken case chooses the Hann-like filter solely because its
PSLR is lower, then places the weak target only seven samples (about 26.2 m)
from the strong one. That position lies inside the wider tapered mainlobe. The
visibility margin stays negative, so the weak target is not revealed. The
failure is a bad filter-selection rule, not a failed taper implementation.

Recovery restores the validated 17-sample scene and recreates the private
noise stream exactly. In practice, recovery could instead select a narrower
response when close-target separation matters more than far-sidelobe dynamic
range. Filter choice must use the expected target geometry, noise, and
detection objective—not PSLR alone.

## Assumptions and limiting cases

- Echoes are stationary, point-like, integer-sample delayed, and zero extended.
  The model omits fractional delay, Doppler, clutter, multipath, propagation
  loss, RF distortion, and calibration error.
- The same target phase is used in the deterministic scene. Other relative
  phases can reinforce or cancel the complex leakage locally; the isolated
  magnitude margin remains a structural comparison, not a detection claim.
- `alpha = 0` is the rectangular matched filter and has the maximum white-noise
  output SNR for the transmitted waveform. `alpha = 1` is the Hann-like
  mismatched filter used here.
- A weak target inside the tapered mainlobe cannot be rescued merely by lower
  sidelobes. Far from the strong response, both filters can have positive
  margin and the rectangular filter's SNR advantage may be preferable.
- Multiplying a tapered output by a constant changes displayed peak amplitude
  and noise amplitude together; it does not recover matched-filter SNR.
- PSLR, -3 dB width, and one-point visibility margin summarize different parts
  of the response. None alone proves that an operational detector resolves a
  target.

## Common interpretation mistakes

- Sidelobes are deterministic waveform response, not automatically extra
  targets and not the same thing as white noise.
- Lower PSLR does not mean narrower mainlobe; tapering usually makes the
  mainlobe wider.
- A 6 dB unnormalized peak-amplitude reduction is not the Hann-like filter's
  SNR loss. The measured weighting loss is about 1.77 dB.
- Normalizing every curve to 0 dB is useful for comparing shapes but hides raw
  peak scale. That is why the script prints SNR loss separately.
- A positive clean leakage margin is not a complete detection guarantee in
  noise, clutter, or arbitrary target phase.
- `20*log10` is used for magnitude ratios; `10*log10` is used for power and SNR
  ratios.

## Dependencies and concept connection

P32 established the explicit LFM phase law, zero-extended echoes, conjugate
time-reversed matched filter, and filter-delay-corrected range axis. P33 keeps
those operations visible and changes only receive weighting and target
separation. It uses base MATLAB and no toolbox. P34 will extend this delay-only
view to simultaneous delay and Doppler mismatch.

Completion means you can select weighting that reveals the weak target and quantify the resolution/SNR cost.

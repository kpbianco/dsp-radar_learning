# P79 walkthrough: Separate the Two Axes Before Trading Sidelobes

The guiding question is: **What controls range and cross-range resolution and sidelobes?**

Run `experiment.m` once. It creates five tagged figure groups and prints
metrics in metres and dB. Work through one transition at a time; avoid judging
the final image before inspecting its two isolated point-response cuts.

## 1. Baseline: identify each coherent record

The fixed controls are `10 GHz`, `200 MHz` bandwidth, a `30 m` aperture,
`0.25 m` platform spacing, and `1000 m` broadside range.

1. In Figure 1, inspect the range cut. Its first minima should sit near
   `+/-0.75 m` because `c/(2B)=0.75 m`.
2. Inspect the cross-range cut separately. Its first minima should sit near
   `+/-0.50 m` because `lambda R0/(2L)=0.50 m`.
3. Compare the sidelobes. Uniform finite records in both dimensions give a
   similar peak sidelobe near `-13.3 dB`.
4. Only then inspect the image. The white crosses are truth locations; the
   visible blobs are sums of the two point-spread functions, not ideal pixels.

Concrete observation question: which axis is narrower in metres, and which
physical record made it narrower?

## 2. Bandwidth sweep: change only range

Figure 2 uses `100`, `200`, and `400 MHz`. Carrier, aperture, platform
positions, target geometry, and aperture weights stay fixed.

- Watch the range mainlobe narrow by about two each time bandwidth doubles.
- Read the measured one-sided first nulls against `c/(2B)`: approximately
  `1.50`, `0.75`, and `0.375 m`.
- Notice that uniform-spectrum peak sidelobe stays near `-13 dB`; more
  bandwidth changes scale, not the rectangular record's normalized shape.
- The cross-range response is deliberately reused unchanged. Do not attribute
  a range improvement to the aperture.

The reviewed script fixes these three approved values so its numerical checks
remain reproducible. Treat the displayed sweep as the controlled experiment;
restore the reviewed file before running its completion checks after any local
exploration.

## 3. Aperture sweep: change only cross-range

Figure 3 uses `10`, `20`, and `30 m` apertures with the same `0.25 m` spacing.
This gives 41, 81, and 121 platform looks and preserves centered endpoints.

- The one-sided first-null scale should fall near `1.5`, `0.75`, and `0.50 m`.
- A longer track accumulates residual phase faster when the image hypothesis
  moves away from the true target, so cancellation starts closer to the peak.
- Bandwidth and the range response remain unchanged.
- Do not say that more looks alone caused the result. Here the physical
  aperture grew while spacing stayed fixed; both angular span and look count
  changed together.

If you want to isolate look count from physical span, that is the sampling
comparison in step 5, not this resolution sweep.

## 4. Windowing: exchange width for sidelobes

Figure 4 compares uniform weights with explicit Hamming weights on exactly the
same 121 positions and `30 m` endpoints.

- The Hamming edge positions contribute only a small fraction of the center.
- Peak sidelobe falls by roughly 29 dB in the reviewed response.
- Half-power width grows from about `0.439 m` to about `0.650 m`.
- The curves are peak-normalized for shape comparison. The printed negative
  coherent-peak gain reminds you that plot normalization is not free SNR.

Prediction before toggling the taper: would lower edge weights make the
effective aperture larger or smaller? Smaller is correct, so the mainlobe
must widen.

## 5. Broken case: undersample the aperture

Figure 5 keeps the same `30 m` physical endpoints but changes spacing through
`0.25`, `1`, and `5 m`. The last case has only seven looks.

1. Inspect the cut. The sparse case creates near-unity replicas about `3 m`
   apart, consistent with `lambda R0/(2d)`.
2. Inspect the sparse image. Several false copies resemble real targets even
   though the target list did not change.
3. Notice that their fine edges are not evidence of good unambiguous
   resolution. A narrow local mainlobe can coexist with disastrous ambiguity.
4. Adding image pixels would only draw the copies more smoothly. Tapering also
   cannot distinguish phase histories that are identical at every retained
   look.

The failure is deterministic and bounded. It does not corrupt a file or
external device.

## 6. Recovery and isolation

Recovery does not process the aliased image. It takes the byte-for-byte
unchanged seeded target scene and freshly focuses it using `0.25 m` platform
spacing. The script asserts exact equality with the original dense response
and image.

This distinction matters operationally: missing spatial measurements cannot
be reconstructed merely by undoing a display operation. Recovery requires an
adequately sampled acquisition or an independently justified prior model.

The private seed sets only target phases. It does not call `rng`, `rand`, or
`randn`, so rerunning the script does not alter the caller's random stream.
Every run first closes old figures tagged `P79`, preventing figure growth.

## 7. Connect the concepts

- P32/P33: frequency support determines compressed range response, and
  weighting trades mainlobe width for sidelobes.
- P61/P62: a finite sampled spatial aperture creates beams and aliases.
- P75: a SAR platform records two-way phase across position.
- P77: correct path compensation makes those samples add coherently.
- P78: a long aperture must also follow the target's range path.
- P80: a sharper aperture response will be more sensitive to motion error.

The concise answer is: bandwidth sets the range scale; wavelength, range, and
aperture length set the cross-range scale; weights set a width/sidelobe/SNR
trade; sampling density sets whether the cross-range field is unambiguous.

## Cancellation, rerun, and rollback

The script has finite foreground loops and no timer, worker, file, network, or
checkpoint. Press Ctrl+C to cancel. A cancellation may leave partial figures
and variables, but no persistent product state. Rerun `experiment.m`; its first
lines close prior tagged figures and rebuild all private results.

Repository rollback removes only the P79 artifacts/test/evidence and restores
only P79's manifest status to `scaffolded`. Preserve P78, future module
entries, personal `.learning/` state, and the operator-managed batch contracts.

## Completion handoff

Use `checks.md`. Completion requires a short teach-back that independently
changes range and cross-range resolution and explains why Hamming taper and
dense plotting cannot solve the same problem.

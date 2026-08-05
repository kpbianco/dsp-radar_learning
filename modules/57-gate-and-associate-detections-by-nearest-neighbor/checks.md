# P57 checks: explain why a report is admissible before assigning it

Guiding question: **Which measurement should update which track?**

## Observation checks

1. **Prediction first:** In Figure 1, what information exists before reports
   are associated?
   - **Correct:** each track has a predicted centre and covariance; the scan
     supplies unlabeled reports.
   - **Incorrect:** each report already carries a trusted track identity.

2. **Gate shape:** Why is Track 1's gate much wider in x than y?
   - **Correct:** its predicted innovation covariance is anisotropic.
   - **Incorrect:** the plot stretches all distances for visibility.

3. **Counterexample:** Why can `D3` be a better Track 1 report than closer `D2`?
   - **Correct:** `D3` lies along a high-uncertainty direction, while `D2`
     crosses a tightly predicted direction and fails the nominal gate.
   - **Incorrect:** nearest neighbor ignores distance entirely.

4. **Matrix:** What do the `G` and `X` markers in Figure 3 mean?
   - **Correct:** `G` means `d^2 <= gamma` for that particular pair; `X` means
     the pair is gated out.
   - **Incorrect:** they label target and clutter truth classes.

5. **Assignments:** Which detections remain unused in the baseline?
   - **Correct:** `D2`, `D4`, and `D6`, all clutter in the retained scoring
     labels.
   - **Incorrect:** every detection must update some track.

## Prediction checks

6. **Tighter gate:** If `gamma` decreases with all arrays fixed, can a
   previously rejected pair become valid?
   - **Correct:** no; the accepted set can only stay the same or shrink.
   - **Incorrect:** yes; a tighter gate pulls distant reports inward.

7. **Broader covariance:** If `P^-` grows while residual and `R` stay fixed,
   what happens to a nonzero residual's normalized distance in this sweep?
   - **Correct:** it falls, and the physical gate grows.
   - **Incorrect:** Euclidean residual metres grow automatically.

8. **Zero prediction covariance:** What controls `S` as `P^-` approaches zero?
   - **Correct:** measurement covariance `R`.
   - **Incorrect:** the gate becomes exactly zero regardless of sensor noise.

9. **Isotropic equal uncertainty:** When do Euclidean and Mahalanobis rankings
   become equivalent?
   - **Correct:** when relevant pairs share innovation covariance proportional
     to the identity.
   - **Incorrect:** whenever there is more than one track.

10. **Shared report:** If two tracks prefer the same detection, may both use it?
    - **Correct:** no; selecting a pair removes its measurement column.
    - **Incorrect:** yes; each track independently takes its minimum.

## Interpretation and failure checks

11. **Units:** What are the units of `d^2` and `gamma`?
    - **Correct:** both are dimensionless.
    - **Incorrect:** metres or square metres.

12. **Ellipse scaling:** Why is `sqrt(gamma)` used in the plot?
    - **Correct:** covariance eigenvalues are variances; physical semi-axis
      lengths are `sqrt(gamma*lambda)`.
    - **Incorrect:** the gate test should compare `d^2 <= sqrt(gamma)`.

13. **Innovation covariance:** Why does `S` contain both `P^-` and `R`?
    - **Correct:** residual uncertainty comes from uncertain prediction and
      noisy measurement.
    - **Incorrect:** `R` can be omitted because the report is observed.

14. **Broken case:** What exactly causes Track 1's clutter assignment?
    - **Correct:** raw Euclidean ranking ignores anisotropy and the missing gate
      permits every pair.
    - **Incorrect:** a new random scene moved the correct target.

15. **Recovery:** What proves the recovery is deterministic?
    - **Correct:** it reuses the same arrays and exactly equals the baseline
      assignment.
    - **Incorrect:** it generates more reports until one happens to work.

16. **Loose gate:** Does admitting more candidates mean detection quality
    improved?
    - **Correct:** no; it increases hypothesis count and clutter opportunity.
    - **Incorrect:** yes; every gated report is a target.

17. **Greedy boundary:** Is the smallest-current-pair rule globally optimal?
    - **Correct:** no; crowded geometry can make greedy choices shortsighted.
    - **Incorrect:** yes; nearest neighbor proves the minimum total cost.

18. **No candidate:** What should happen when a track has no valid report?
    - **Correct:** it remains unassigned for this association step.
    - **Incorrect:** the farthest report must be forced into the update.

## Safety, resource, and recovery checks

19. **Malformed covariance:** What should happen if an innovation covariance is
    singular or nonsymmetric?
    - **Correct:** reject it before computing a distance or assignment.
    - **Incorrect:** take an explicit inverse and accept any finite result.

20. **Resource bound:** What limits the reviewed work?
    - **Correct:** three tracks, six reports, three reviewed cases per sweep,
      nine association passes, 162 pair slots, six figures, and 73 ellipse
      points; validation caps a sweep at five cases.
    - **Incorrect:** an unbounded report stream is processed in the background.

21. **Cancellation:** What is the recovery after Ctrl+C?
    - **Correct:** rerun from the top; private seeded inputs and local arrays
      reconstruct the same baseline without persisted experiment state.
    - **Incorrect:** resume a hidden worker or partial assignment file.

22. **Responsibility boundary:** Should P57 initiate a new track from `D2`?
    - **Correct:** no; P58 owns initiation, confirmation, coasting, and deletion.
    - **Incorrect:** every unassigned detection immediately becomes permanent.

23. **Claim boundary:** What do repository checks establish?
    - **Correct:** static structure and an independent host-language oracle;
      MATLAB runtime, plots, hardware, field, and operational performance need
      separate evidence.
    - **Incorrect:** static tests prove real-time radar performance.

## Completion checklist

- [ ] I identified the baseline mapping `T1->D3`, `T2->D1`, `T3->D5`.
- [ ] I explained why closer clutter `D2` fails Track 1's nominal gate.
- [ ] I distinguished residual metres, covariance square metres, and
      dimensionless squared Mahalanobis distance.
- [ ] I described the missed-update versus clutter-ambiguity gate tradeoff.
- [ ] I explained how row and column removal enforce one-to-one association.
- [ ] I ran both sweeps and the broken/recovery comparison.

## Short teach-back rubric

In two or three sentences, explain why nearest in metres can be the wrong
measurement, what gating removes, and how the one-to-one greedy rule uses the
remaining candidates. A complete answer mentions `S = H P^- H' + R`,
dimensionless Mahalanobis distance, and the fact that unused reports or tracks
are valid outputs rather than forced assignments.

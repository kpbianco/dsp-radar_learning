# P59 checks: separate a track slot from a physical target identity

Guiding question: **Why do simple nearest-neighbor trackers swap identities?**

## Observation checks

1. **Crossing geometry:** What becomes ambiguous near scan 13?
   - **Correct:** the two position predictions and reports overlap within their
     measurement uncertainty.
   - **Incorrect:** the truth IDs disappear from the report packet.

2. **Baseline history:** When does the reviewed position-only identity swap?
   - **Correct:** both slots change truth identity after scan 13 and remain
     swapped through scan 25.
   - **Incorrect:** the tracks are deleted and recreated at scan 14.

3. **Two metrics:** Why are there 24 wrong links but two transitions?
   - **Correct:** two slots are wrong for 12 scans, but each slot changes
     identity only once.
   - **Incorrect:** every wrong link creates a new track.

4. **Report order:** Does report column 1 always mean Truth A?
   - **Correct:** no; column order alternates by scan and association cannot use
     the separate audit truth array.
   - **Incorrect:** yes; MATLAB column position is a physical identity.

5. **Velocity result:** What changed between Figures 2 and 3?
   - **Correct:** a normalized velocity residual was added to the association
     cost; position reports and the state correction stayed the same.
   - **Incorrect:** the velocity-aware case used a luckier random seed.

## Prediction checks

6. **More position noise:** What should happen with all other controls fixed?
   - **Correct:** the pair costs overlap more often, raising reviewed failure
     frequency and usually extending wrong histories.
   - **Incorrect:** normalization makes noise irrelevant.

7. **More closest separation:** What should happen?
   - **Correct:** spatial evidence strengthens and crossing ambiguity falls.
   - **Incorrect:** track identity becomes a field in the detection.

8. **Zero feature weight:** What does `lambda_v = 0` produce?
   - **Correct:** exactly the position-only cost.
   - **Incorrect:** a velocity-only tracker.

9. **Infinite velocity uncertainty:** What happens as `sigma_v` grows very
   large?
   - **Correct:** the normalized velocity term vanishes toward position-only
     behavior.
   - **Incorrect:** velocity becomes infinitely trustworthy.

10. **Identical features:** If both targets have identical measured position,
    velocity, amplitude, and class, can any tie rule recover truth identity?
    - **Correct:** no; the permutation is unobservable from those data.
    - **Incorrect:** yes; always choose the first report.

11. **Update interval:** Why does the reviewed failure rate fall as `dt`
    increases?
    - **Correct:** fixed scan count places adjacent samples farther from the
      crossing and `(beta/dt)r` reduces residual-driven velocity correction;
      the combined result is model-specific.
    - **Incorrect:** slow updates universally improve tracking.

## Interpretation and failure checks

12. **Units:** What are the units of `Jp`, the velocity term, and `J`?
    - **Correct:** all are dimensionless after division by their noise
      variances.
    - **Incorrect:** metres squared plus metres squared per second squared.

13. **Feedback:** Why can one wrong decision persist?
    - **Correct:** the selected report corrects position and velocity, changing
      the next prediction toward the other target.
    - **Incorrect:** the truth scorer edits the track state.

14. **One-to-one boundary:** What does row-and-column removal guarantee?
    - **Correct:** no track or report is used more than once in one scan.
    - **Incorrect:** the globally minimum total assignment and correct identity.

15. **Broken case:** What makes the broken estimates coalesce?
    - **Correct:** independent row minima let both tracks consume the same
      report on 12 scans.
    - **Incorrect:** the targets physically merge into one object.

16. **Recovery:** Why is exact array equality important?
    - **Correct:** it proves the rule was restored on identical inputs rather
      than finding a favorable new noise record.
    - **Incorrect:** approximate recovery would prove hardware performance.

17. **Lifecycle:** Can confirmation logic alone repair this swap?
    - **Correct:** no; both tracks remain valid and receive hits. This is an
      upstream association error.
    - **Incorrect:** P58 automatically reads truth identity on every hit.

18. **Richer feature:** Does velocity guarantee correct identity?
    - **Correct:** no; it lowers failures under the reviewed model but can be
      identical, noisy, biased, or overweighted.
    - **Incorrect:** any extra cost term must improve every scene.

## Safety, resource, compatibility, and recovery checks

19. **Malformed input:** What happens to a NaN noise scale or zero `dt`?
    - **Correct:** validation rejects it before random work or figures.
    - **Incorrect:** the tracker silently clips it.

20. **Resource bound:** What bounds the experiment?
    - **Correct:** two tracks/reports, 25 scans, 200 trials, three cases in each
      of three sweeps, at most 3,605 association passes, 360,500 pair
      evaluations, 200 standard-normal values per scene, 360,200 across the
      baseline and nine sweep cases, and six figures.
    - **Incorrect:** it starts an unbounded stream or background worker.

21. **Cancellation:** What should you do after Ctrl+C?
    - **Correct:** close only `P59` figures if needed and rerun from the top;
      private seeds reconstruct the same arrays.
    - **Incorrect:** resume a hidden partial association file.

22. **Compatibility:** What permanent prerequisite may a P59 test assert?
    - **Correct:** P58 is implemented and P59 has its exact canonical identity.
    - **Incorrect:** P59 must remain the latest module and P60 must remain
      scaffolded forever.

23. **Claim boundary:** What do repository checks establish?
    - **Correct:** static structure plus an independent bounded oracle, not
      MATLAB runtime, hardware, field, or operational performance.
    - **Incorrect:** Python tests prove rendered MATLAB figures and radar safety.

## Completion checklist

- [ ] I reproduced 24 wrong links and two transitions for seed 5908.
- [ ] I distinguished identity swap, coalescence, and track deletion.
- [ ] I explained why position and velocity terms must be normalized.
- [ ] I compared failure frequency with wrong-link duration.
- [ ] I interpreted all three one-variable sweeps within their model limits.
- [ ] I recovered exactly from the duplicate-report broken case.

## Short teach-back rubric

In two or three sentences, explain why a locally nearest report can redirect a
track's future history, what one-to-one selection does and does not guarantee,
and why a calibrated velocity or amplitude feature can lower—but not
eliminate—identity swaps. A complete answer mentions ambiguous crossing
geometry, update feedback, normalized uncertainty, and the unobservable
identical-feature limit.

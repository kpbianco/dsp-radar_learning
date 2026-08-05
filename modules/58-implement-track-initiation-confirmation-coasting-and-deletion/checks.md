# P58 checks: explain which evidence earns persistence

Guiding question: **How does a radar avoid creating permanent tracks from single false alarms?**

## Observation checks

1. **Input record:** What does the manager know about each plotted report?
   - **Correct:** only its scan, Cartesian position, and validity; truth colors
     are joined later for scoring.
   - **Incorrect:** every report arrives labeled target or false alarm.

2. **Initiation:** What happens to an unassigned false report?
   - **Correct:** it initiates a tentative track with one hit in its history.
   - **Incorrect:** it is discarded because the tracker knows it is false.

3. **Confirmation scan:** Why does the target confirm on scan 7?
   - **Correct:** scans 4, 5, and 7 give three hits within the latest four
     scans despite the miss on scan 6.
   - **Incorrect:** the reports must be consecutive, so scan 6 resets all
     evidence.

4. **False tracks:** Why do the eight reviewed false tracks not confirm?
   - **Correct:** their separated isolated reports never reach score 3 in a
     four-scan window.
   - **Incorrect:** initiation is disabled at false-alarm positions.

5. **Lifecycle plot:** What does code 4 mean?
   - **Correct:** deletion occurred on that scan; later zero means inactive.
   - **Incorrect:** the track had four hits on that scan.

6. **Score plot:** Why may the confirmed target's score fall below `M`?
   - **Correct:** `M-of-N` controls one-way promotion; confirmed maintenance is
     governed by consecutive misses.
   - **Incorrect:** the track must silently return to tentative.

## Prediction checks

7. **One-of-four:** What happens if only `M` changes from 3 to 1?
   - **Correct:** target declaration is immediate and all eight isolated false
     tracks also confirm.
   - **Incorrect:** `N=4` still requires four observations before promotion.

8. **Four-of-four:** What happens after the early scan-6 miss?
   - **Correct:** the first tentative target track expires; a replacement can
     later collect four hits and confirm on scan 11.
   - **Incorrect:** stricter confirmation always preserves the same ID.

9. **Coast boundary:** With `L=2`, what happens on misses one, two, and three?
   - **Correct:** the first two coast; the third deletes.
   - **Incorrect:** the second deletes because `c >= L`.

10. **Reacquisition:** What does the scan-14 hit do to the miss counter?
    - **Correct:** it resets consecutive misses to zero and returns the same ID
      from coasting to confirmed.
    - **Incorrect:** it starts a new tentative track because score is below M.

11. **No coasting:** What does `L=0` do?
    - **Correct:** it deletes a confirmed track on the first miss and splits
      the reviewed target into two confirmed segments.
    - **Incorrect:** zero means coast forever without prediction.

12. **Long coasting:** Does `L=30` prove the target still exists?
    - **Correct:** no; it only prevents deletion within this 30-scan record.
    - **Incorrect:** persistence of state is evidence of physical persistence.

## Interpretation and failure checks

13. **M-of-N meaning:** Is 3-of-4 a probability?
    - **Correct:** no; it is a deterministic rule applied to a binary hit
      history. Probability enters only through a separate detection model.
    - **Incorrect:** the score equals 75 percent target probability.

14. **Initiation versus maintenance:** Why use different failure rules?
    - **Correct:** a weak new hypothesis must earn credibility, while an
      established target may deserve bounded prediction through a dropout.
    - **Incorrect:** all tracks should be deleted whenever score is below M.

15. **One-to-one input:** Can an assigned report also initiate a new track?
    - **Correct:** no; the chosen detection column is marked used.
    - **Incorrect:** yes; initiation is independent of association.

16. **Prediction-only coast:** What measurement corrects position on a coast?
    - **Correct:** none; the prior velocity propagates position.
    - **Incorrect:** a numeric zero or the last report is inserted.

17. **Broken case:** Why do false tracks become permanent over the record?
    - **Correct:** 1-of-1 grants immediate confirmation and the horizon-length
      coast allowance prevents stale deletion.
    - **Incorrect:** the false-alarm generator changes to make repeated targets.

18. **Recovery:** What makes the recovery meaningful?
    - **Correct:** it reuses identical detections and compares every
      decision-bearing result field with the baseline.
    - **Incorrect:** it sets `recovery_exact=true` after deleting false IDs.

19. **Association boundary:** Would this lifecycle logic prevent an ID swap at
    a target crossing?
    - **Correct:** no; P59 examines that upstream association failure.
    - **Incorrect:** confirmation proves an association can never be wrong.

20. **False-confirm approximation:** Which binomial expression applies after a
    false track has already been initiated, and when is it only an
    approximation?
    - **Correct:** conditioning on the birth hit leaves `N-1` scans in which at
      least `M-1` further hits are needed; correlation, changing gate
      probability, or coupled association makes even that model approximate.
    - **Incorrect:** use the unconditional `M` hits in `N` scans expression and
      treat it as exact for every clutter and tracker geometry.

## Safety, malformed-input, resource, and recovery checks

21. **Malformed record:** What should happen when a valid report is `NaN`, or
    an unused slot contains a finite value?
    - **Correct:** reject the record before lifecycle processing.
    - **Incorrect:** silently convert either value into a missed detection.

22. **Malformed policy:** What should happen for `M=0`, `M>N`, fractional
    counts, nonfinite gains, or negative `L`?
    - **Correct:** stop with a named validation error.
    - **Incorrect:** round, clip, or enlarge a ceiling automatically.

23. **Resource bound:** What limits the reviewed work?
    - **Correct:** 30 scans, 2 reports per scan, 20 IDs, 9 runs, 10,800 pair
      slots, and 6 figures; validation precedes random work and history arrays.
    - **Incorrect:** an unbounded detection stream continues in a worker.

24. **Isolation:** Does running this experiment change learner progress or the
    MATLAB global random stream?
    - **Correct:** no; it has no learner/file side effect and uses private
      arithmetic generators.
    - **Incorrect:** it stores confirmation history under `.learning/`.

25. **Cancellation:** What is the recovery after Ctrl+C?
    - **Correct:** rerun from the top to rebuild private seeded inputs and local
      track arrays; no external partial state needs rollback.
    - **Incorrect:** resume a hidden timer, worker, or partial track file.

26. **Compatibility:** What does base MATLAB and R2016b mean here?
    - **Correct:** no tracking toolbox is required, and local script functions
      need R2016b or later; actual MATLAB execution still requires evidence.
    - **Incorrect:** static Python tests prove all MATLAB versions executed it.

27. **Claim boundary:** What do repository checks establish?
    - **Correct:** static structure, a deterministic host-language oracle, CLI
      isolation, and documented contracts—not MATLAB figures, hardware/HIL,
      field, or real-time performance.
    - **Incorrect:** passing CI validates an operational radar tracker.

## Completion checklist

- [ ] I identified the target's tentative, confirmed, coasting, and deletion
      transitions at scans 4, 7, 12-13, 14, and 27.
- [ ] I explained why a birth hit counts but one isolated false alarm cannot
      pass the reviewed 3-of-4 policy.
- [ ] I predicted the strictness/latency tradeoff in the `M` sweep.
- [ ] I predicted the dropout/stale-state tradeoff in the `L` sweep.
- [ ] I explained why confirmed maintenance does not reuse `score < M`.
- [ ] I ran the broken policy and exact deterministic recovery.

## Short teach-back rubric

In two or three sentences, answer the guiding question. A complete answer says
that an unassigned detection first creates only a tentative hypothesis,
`M-of-N` repeated hits earn confirmation, a confirmed track may coast through
at most `L` consecutive misses, and deletion on miss `L+1` bounds stale state.
It also distinguishes truth-free association/lifecycle decisions from the
truth labels used only to score this synthetic experiment.

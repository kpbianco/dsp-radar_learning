# P72 checks: Pair the Beats Carefully

## Guiding question

How can opposite chirp slopes disentangle delay and Doppler?

1. What mixer and velocity convention does this lesson use?

   **Correct:** `tx .* conj(rx)`, with positive velocity approaching and
   positive carrier Doppler.

2. What are the signed slopes?

   **Correct:** `+S` on the up leg and equal-magnitude `-S` on the down leg.

3. What is the up-leg beat equation?

   **Correct:** `f_up = S tau - f_d`.

4. What is the down-leg beat equation?

   **Correct:** `f_down = -S tau - f_d`.

5. Which physical term changes sign with chirp slope?

   **Correct:** The delay term `S tau`.

6. Which physical term keeps its sign?

   **Correct:** Carrier Doppler `-f_d` in the declared dechirp convention.

7. How does beat difference recover delay?

   **Correct:** `(f_up - f_down)/2 = S tau`.

8. How does beat sum recover Doppler?

   **Correct:** `-(f_up + f_down)/2 = f_d`.

9. What is the range formula?

   **Correct:** `R = c(f_up - f_down)/(4S)`.

10. What is the velocity formula?

    **Correct:** `v = -lambda(f_up + f_down)/4`.

11. What are the baseline ideal signed beats?

    **Correct:** About `+139.733 kHz` up and `-160.267 kHz` down.

12. What baseline range and velocity should they recover?

    **Correct:** `45 m` and `+20 m/s` approaching.

13. Why must the down beat remain signed?

    **Correct:** Its negative sign carries the slope reversal used by the
    sum/difference solve; absolute value changes the equations.

14. What changes during the range sweep?

    **Correct:** Only target range and therefore round-trip delay.

15. What should the range sweep do to the beats?

    **Correct:** Move them apart symmetrically as `S tau` grows.

16. What should remain fixed in the range sweep?

    **Correct:** The beat sum and recovered velocity, apart from seeded noise.

17. What changes during the velocity sweep?

    **Correct:** Only signed radial velocity and therefore Doppler.

18. What should velocity do to the beats?

    **Correct:** Translate both signed beats together by the same `-f_d`
    change.

19. What should remain fixed in the velocity sweep?

    **Correct:** Beat separation and recovered range, apart from seeded noise.

20. What happens at zero velocity?

    **Correct:** `f_down = -f_up`, their sum is zero, and recovered velocity is
    zero.

21. Why use two distinct private noise streams?

    **Correct:** Identical leg noise could cancel artificially in one linear
    combination and make the solve look better than independent measurements.

22. Must absolute error increase at every noise-sweep step?

    **Correct:** No. A single fixed realization can fluctuate; zero-noise
    exactness and the visible trend are the reviewed observations.

23. What does zero delay produce?

    **Correct:** Both beats equal `-f_d`, so their difference and recovered
    range are zero.

24. Why is zero slope invalid?

    **Correct:** The two equations lose their independent delay terms and the
    range formula divides by zero.

25. What if either signed beat reaches `fs/2` in magnitude?

    **Correct:** It aliases, so the pre-alias frequency cannot be trusted by
    the solve.

26. Why require at least two common overlap samples?

    **Correct:** The lag-one signed-tone estimator requires a sample pair, and
    both target echoes must be present for the reviewed measurement.

27. What fails if adjacent legs see appreciably different target states?

    **Correct:** The shared `tau` and `f_d` assumption; acceleration or range
    migration biases the simple two-equation solve.

28. What does the broken multi-target case do?

    **Correct:** It pairs each detected up beat with the down beat belonging to
    the other target.

29. Why do wrong pairs still produce answers?

    **Correct:** Any two signed frequencies exactly solve two equations, even
    when they did not come from one physical target.

30. Can a zero equation residual identify the correct pairing?

    **Correct:** No. Every pairing satisfies its constructed two-equation
    system.

31. What changes during recovery?

    **Correct:** Only the down-beat association permutation; detected beats and
    all underlying data remain unchanged.

32. What extra information can resolve association?

    **Correct:** Examples include another ramp, track continuity, angle,
    amplitude, or a justified feasible-state gate.

33. Does sorting both beat lists solve association generally?

    **Correct:** No. Frequency order is not a target identity label.

34. Does zero-padding resolve close targets or pairing?

    **Correct:** No. It interpolates the finite spectrum and adds no physical
    observation.

35. What external state can cancellation leave behind?

    **Correct:** None. Partial figures and workspace arrays can remain, but no
    file transaction, worker, timer, network request, or hardware operation is
    started.

36. What are the reviewed resource ceilings?

    **Correct:** At most 5,000 samples, seven cases per sweep, three targets,
    20,000 private-generator values per request, 350,000 retained numeric
    values, and seven tagged figure groups.

37. What runtime compatibility is targeted?

    **Correct:** Base MATLAB R2016b or newer with no optional toolbox; static
    checks alone do not prove that runtime compatibility.

38. Does this deterministic simulation prove operational radar performance?

    **Correct:** No. It is a bounded synthetic first-order learning model.

## Completion checklist

- I can state both signed beat equations and conventions.
- I can explain why difference yields range and sum yields velocity.
- I can predict the one-variable range, velocity, and noise observations.
- I can retain beat sign through DC and Nyquist reasoning.
- I can diagnose cross-target beat pairing and same-data recovery.
- I can name at least one additional association cue.
- I can state the sequential-leg and runtime-evidence boundaries.

## Short teach-back rubric

In about six sentences: state both signed beat equations, explain what slope
reversal changes and preserves, give the range and velocity combinations,
describe one sweep, explain why wrong multi-target pairs create ghosts, and
name an additional association cue. Do not claim sorting alone solves pairing
or that static validation is MATLAB, RF, hardware, or field evidence.

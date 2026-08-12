# P73 checks: Which Phase Came from Space?

## Guiding question

How do multiple transmit and receive channels create more spatial samples?

1. What is the virtual-position equation?

   **Correct:** `x_virtual,pq = x_tx,p + x_rx,q`.

2. Why is it a sum rather than an average?

   **Correct:** The directional round-trip path contains one transmit-position
   contribution and one receive-position contribution.

3. Should another monostatic factor of two multiply the position sum?

   **Correct:** No. The two legs are already represented by the TX and RX
   terms; Doppler's factor two is a separate law.

4. What are the four reviewed RX positions?

   **Correct:** `[0, 0.5, 1.0, 1.5] lambda`.

5. What are the two reviewed TX positions?

   **Correct:** `[0, 2.0] lambda`.

6. What virtual positions do those sums create?

   **Correct:** `[0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5] lambda`.

7. How many simultaneous receive channels exist?

   **Correct:** Four. The eight virtual channels combine two sequential TX
   slots with those four RX channels.

8. Does `N_tx N_rx` always equal the number of unique phase centers?

   **Correct:** No. Different pairs can produce duplicate position sums.

9. What physical aperture does RX-only processing use?

   **Correct:** `1.5 lambda`.

10. What aperture does the reviewed virtual array use?

    **Correct:** `3.5 lambda`.

11. Why is the virtual beam narrower?

    **Correct:** A direction change accumulates more residual phase across the
    larger aperture, so the coherent match falls away faster.

12. What are the approximate baseline half-power widths?

    **Correct:** About `27.8 deg` for four RX positions and `13.5 deg` for the
    eight virtual positions at the `+18 deg` target.

13. What processing-point convention does P73 use?

    **Correct:** A selected FMCW range bin after `tx .* conj(rx)` dechirping.

14. What is its spatial steering sign?

    **Correct:** `exp(-j 2 pi x sin(theta)/lambda)`.

15. Why did P61 use the opposite spatial sign?

    **Correct:** P61 modeled the raw analytic receive snapshot; dechirping with
    `tx .* conj(rx)` conjugates the received phase.

16. What is the explicit scan operation?

    **Correct:** Construct `w=a(theta)/M`, apply the Hermitian sum `w^H x`, and
    average output magnitude squared across cycles.

17. What changes in the first sweep?

    **Correct:** Only the symmetric angular separation of two equal incoherent
    targets.

18. What stays fixed in that sweep?

    **Correct:** Scene center, target powers, arrays, wavelength, and scan grid.

19. What happens at `8 deg` separation?

    **Correct:** Both receive-only and virtual responses remain merged.

20. What happens at `16 deg` separation?

    **Correct:** The virtual response has two maxima and a midpoint dip while
    the four-RX response remains merged.

21. What happens at `28 deg` separation?

    **Correct:** Both arrays resolve the pair, with a much deeper virtual dip.

22. Did a denser angle grid create that resolution?

    **Correct:** No. Both curves use the same grid; the physical aperture
    changes their finite spatial response.

23. What is the positive-approaching Doppler law?

    **Correct:** `f_d = 2v/lambda`.

24. What temporal phase does the dechirped sample carry?

    **Correct:** `-2 pi f_d t`.

25. What phase separates the two TX groups?

    **Correct:** `Delta_phi_TDM = -2 pi f_d T_slot`.

26. What changes in the velocity sweep?

    **Correct:** Only signed radial velocity.

27. What remains fixed in the velocity sweep?

    **Correct:** True angle, geometry, timing, SNR, cycles, and deterministic
    noise realization.

28. What happens at zero velocity?

    **Correct:** Inter-TX motion phase is zero, so the uncompensated and
    compensated angles agree with truth apart from seeded noise.

29. Under this convention, which way does positive velocity bias the naive angle?

    **Correct:** Toward a more-positive broadside-referenced angle.

30. Why can an angle scanner not label the phase as temporal?

    **Correct:** Once sequential samples are arranged by virtual position, the
    scanner only sees channel phase and assumes it all came from geometry.

31. How is Doppler estimated without mixing geometry and time?

    **Correct:** Compare each channel with itself one complete TDM cycle later
    and average the lag-one conjugate products.

32. What is the Doppler estimator?

    **Correct:** `f_d_hat = -angle(sum(conj(x[l]) x[l+1]))/(2 pi T_cycle)`.

33. How is each TX slot compensated?

    **Correct:** Multiply by `exp(+j 2 pi f_d_hat t_slot)`.

34. What is the reviewed broken-case velocity and Doppler?

    **Correct:** `+10 m/s` approaching and about `+5.133 kHz`.

35. What inter-TX phase does it create?

    **Correct:** About `-1.290 rad` for `40 us` slot separation.

36. What changes during recovery?

    **Correct:** Only a derived compensated array is created from the measured
    Doppler and known slot times; the broken measurement is unchanged.

37. Why can the same-TX Doppler estimate alias?

    **Correct:** Each channel is sampled once per full TDM cycle, so its phase
    increment is unique only inside half that sampling frequency.

38. What is the reviewed unambiguous velocity condition?

    **Correct:** `|v| < lambda/(4 T_cycle)`; the `+/-10 m/s` sweep stays inside
    the `80 us`-cycle limit.

39. Does a `2 pi` inter-TX phase prove zero motion?

    **Correct:** No. A nonzero motion phase can wrap to the same complex value.

40. Why must positions and samples be reordered together?

    **Correct:** Sorting only positions assigns measurements to the wrong
    steering phases and corrupts the scan.

41. What assumptions does compensation make?

    **Correct:** Known slot timing, one associated target Doppler, constant
    radial velocity, calibrated channels, and negligible migration during the
    dwell.

42. What external state can cancellation leave behind?

    **Correct:** None. Partial figures and workspace arrays can remain, but no
    file transaction, worker, timer, network request, or hardware operation is
    started.

43. What are the reviewed resource ceilings?

    **Correct:** 32 virtual channels, 128 TDM cycles, 2,001 scan angles, seven
    cases per sweep, 20,000 private values per request, 500,000 retained numeric
    values, and five tagged figure groups.

44. What runtime compatibility is targeted?

    **Correct:** Base MATLAB R2016b or newer with no optional toolbox; static
    checks alone do not prove runtime compatibility.

45. Does this simulation validate a physical MIMO radar?

    **Correct:** No. It is a bounded ideal synthetic model, not RF, antenna,
    hardware/HIL, real-time, field, or operational validation.

## Completion checklist

- I can draw all physical and virtual positions and explain the sums.
- I can distinguish simultaneous RX channels from sequential virtual samples.
- I can connect virtual aperture with beamwidth and the separation sweep.
- I can state the dechirped spatial and temporal sign conventions.
- I can predict the velocity sweep's uncompensated angle direction.
- I can explain the same-TX Doppler estimate and same-data compensation.
- I can state the uniqueness, aliasing, compatibility, and claim boundaries.

## Short teach-back rubric

In about six sentences: state the virtual-position sum, compare physical and
virtual apertures, describe the `16 deg` pair, write the inter-TX motion phase,
explain why it biases angle, and describe same-TX Doppler recovery on unchanged
data. Do not call virtual channels simultaneous or claim static simulation is
MATLAB, RF, hardware, or field evidence.

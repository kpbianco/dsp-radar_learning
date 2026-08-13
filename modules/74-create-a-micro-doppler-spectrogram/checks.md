# Checks: bulk and micro-Doppler interpretation

## Guiding question

How do rotating or swinging target parts produce time-varying Doppler around bulk motion?

Use these as a conversation after inspecting the figures. Answers are included
so the checks test interpretation rather than memory of MATLAB syntax.

## Observation and prediction checks

1. What are the three baseline scatterers?

   **Correct:** One strong steadily approaching torso and two weaker limbs
   swinging in opposite phase.

2. What does positive radial velocity mean here?

   **Correct:** Approaching the radar.

3. What is the physical Doppler law?

   **Correct:** `f_d = 2v/lambda = 2v f_c/c` for the displayed
   positive-approaching convention.

4. What is the `24 GHz` wavelength?

   **Correct:** `0.0125 m`, or `12.5 mm`.

5. What bulk Doppler does `+1.2 m/s` produce?

   **Correct:** `+192 Hz`.

6. What Doppler excursion does a `2 m/s` limb swing produce?

   **Correct:** `+/-320 Hz` around bulk.

7. What are the baseline limb extrema?

   **Correct:** About `-128 Hz` and `+512 Hz`.

8. Does one target range cell imply one component velocity?

   **Correct:** No. Several scattering parts can occupy one cell and carry
   different instantaneous radial velocities.

9. Why integrate velocity before forming phase?

   **Correct:** Phase is proportional to displacement, so time-varying Doppler
   is the phase derivative rather than a frequency value multiplied directly
   by absolute time.

10. What error appears in `exp(-j 2 pi f_d(t)t)`?

    **Correct:** Differentiation creates an unintended `t df_d/dt` term.

11. What is the raw selected-range-bin phase convention?

    **Correct:** `x_i(t) = a_i exp(-j 4 pi d_i(t)/lambda + j phi_i)`, so an
    approaching component rotates at negative raw slow-time frequency.

12. Why is displayed approaching Doppler positive?

    **Correct:** The script reverses both the shifted FFT/STFT data and axis;
    it does not merely relabel a negative-frequency result.

13. What does the raw composite phase show?

    **Correct:** Coherent phase evolution of the summed torso, limbs, and
    noise—not a clean phase history for one named body part.

14. Why can composite phase jump?

    **Correct:** Component phasors can nearly cancel, making the sum's phase
    ill-conditioned.

15. What does the dwell-wide FFT preserve?

    **Correct:** Aggregate frequency content over the observation.

16. What does the dwell-wide FFT discard?

    **Correct:** When within the dwell each component velocity occurred.

17. Is every sideband line a separate constant-velocity target?

    **Correct:** No. Periodic phase modulation of one scatterer creates a
    sideband pattern.

18. What does each STFT frame do?

    **Correct:** Extracts a finite segment, multiplies it by an explicit Hann
    window, computes a two-sided FFT, shifts it, and maps raw frequency to
    signed physical Doppler.

19. Where is each frame timestamp placed?

    **Correct:** At the center of its window.

20. What is the baseline window duration?

    **Correct:** `512/4800 = 106.7 ms`.

21. What is the baseline torso signature?

    **Correct:** A near-horizontal ridge around `+192 Hz`.

22. What is the baseline limb signature?

    **Correct:** Periodic energy tracks extending above and below bulk Doppler.

23. Why can a brightest-pixel ridge exchange identity?

    **Correct:** Tracks cross and coherent components interfere, so local
    maxima need not stay attached to one physical scatterer.

24. What changes in the swing-speed sweep?

    **Correct:** Only peak limb speed.

25. What stays fixed in that sweep?

    **Correct:** Bulk speed, carrier, swing rate, amplitudes, observation,
    STFT settings, and deterministic additive-noise samples and scale.

26. Predict the extents for swing speeds `[1, 2, 3] m/s`.

    **Correct:** `+/-[160, 320, 480] Hz` around the fixed `+192 Hz` bulk.

27. Does faster swinging move the bulk ridge?

    **Correct:** No.

28. Does faster swinging change the `1.5 Hz` repetition rate?

    **Correct:** No; speed amplitude and periodic rate are separate controls.

29. What changes in the carrier sweep?

    **Correct:** Only carrier frequency.

30. Why do hertz shifts grow with carrier?

    **Correct:** Wavelength shortens and `f_d = 2v f_c/c`.

31. Do the physical velocities grow in the carrier sweep?

    **Correct:** No; converting each frequency with its own wavelength recovers
    the same velocities.

32. Why must the highest-carrier case be checked against slow-time Nyquist?

    **Correct:** Its hertz shift is largest and could fold into a false signed
    component velocity.

33. What changes in the window sweep?

    **Correct:** Only STFT window and its proportional overlap; the complex
    measurement and FFT display length are unchanged.

34. What does a shorter window improve?

    **Correct:** Localization of rapid changes in time.

35. What does a shorter window worsen?

    **Correct:** The finite-window frequency response becomes broader.

36. What does a longer window improve for a constant tone?

    **Correct:** It narrows the finite-observation frequency response.

37. What does a longer window do to curved limb motion?

    **Correct:** It averages a larger part of the swing into each frame and
    smears time variation.

38. Does fixed zero-padding make all windows equally resolving?

    **Correct:** No. It keeps the display grid dense; physical response still
    depends on window duration.

39. What does overlap mainly control?

    **Correct:** The density of reported frame times, not independent physical
    resolution.

40. What is the intentionally broken operation?

    **Correct:** `abs` is applied to the complex slow-time record before STFT.

41. What does magnitude-only processing remove?

    **Correct:** Absolute signed phase rotation, including the common bulk
    Doppler.

42. Must the broken plot be blank?

    **Correct:** No. Relative coherent amplitude beating can remain near zero.

43. What changes during recovery?

    **Correct:** Only the processing input switches back to the saved complex
    samples; the measurement is unchanged and not regenerated.

44. What happens when `v_swing = 0`?

    **Correct:** Periodic spread vanishes and all three components share bulk
    Doppler, subject to coherent amplitude addition.

45. What happens when `v_bulk = 0`?

    **Correct:** The torso ridge moves to zero and limbs cross positive and
    negative physical Doppler.

46. What happens as carrier tends toward zero?

    **Correct:** Doppler in hertz shrinks for fixed physical velocity.

47. Why is zero swing rate rejected rather than treated as a limit?

    **Correct:** The reviewed displacement expression divides by swing rate;
    silently substituting a different motion model would hide malformed input.

48. What malformed shapes are rejected?

    **Correct:** Controls requiring row vectors reject nested/column forms, and
    scalar controls reject nonscalar, nonnumeric, complex, or nonfinite values.

49. What resource bounds are checked before processing?

    **Correct:** Samples, FFT lengths, frame count, sweep cases, private random
    values, predicted and measured complete live-workspace storage, figures,
    and worst-case Doppler Nyquist across both baseline and sweep controls.

50. What can `Ctrl+C` leave behind?

    **Correct:** Partial workspace arrays and figures only; there is no worker,
    timer, file transaction, network request, hardware operation, or external
    persistent state to cancel or recover.

51. How do you recover from cancellation or a corrected control?

    **Correct:** Close partial figures if desired and rerun from the top; visible
    seeds reproduce the same private noise.

52. What is the repository rollback boundary?

    **Correct:** Remove P74-owned implementation/tests/evidence and restore only
    P74 manifest/catalog status, preserving P73, future identities, learner
    state, and operator-managed contracts.

53. What runtime compatibility is targeted?

    **Correct:** Base MATLAB R2016b or newer with no optional toolbox.

54. Does static validation prove MATLAB figures or numerical execution?

    **Correct:** No. MATLAB runtime and rendered plots require separate named
    evidence.

55. Does this validate human gait, rotor classification, RF hardware, or field radar?

    **Correct:** No. It is a deterministic bounded point-scatterer learning
    simulation, not physical, hardware/HIL, bench, real-time RT1/RT2, field,
    Unreal, signing, deployment, staging, production, or operational evidence.

## Completion checklist

- I can identify bulk Doppler and periodic component tracks.
- I can turn component velocity into integrated phase with the correct sign.
- I can explain why a full-dwell FFT loses timing.
- I can distinguish speed scaling from carrier-frequency scaling.
- I can state the STFT time-frequency tradeoff without crediting zero-padding.
- I can explain magnitude-only failure and unchanged-I/Q recovery.
- I can state Nyquist, interference, resource, compatibility, and evidence limits.

## Short teach-back rubric

In about six sentences: write the velocity-to-Doppler law, describe the torso
and limb signatures, compare the speed and carrier sweeps, explain the STFT
window tradeoff, and recover the broken magnitude-only case from unchanged I/Q.
The explanation must distinguish simulation/static evidence from MATLAB
runtime, rendered figures, and physical-radar validation.

# P15: Use a Spectrogram to See Time-Varying Frequency

**Phase 2: Fourier, Spectral, and I/Q Intuition**  
**Status:** Scaffolded; implementation batch `P15` is pending

## Guiding question

How do window duration and overlap control time-frequency visibility?

## Experiment

Create a signal containing a steady tone, a chirp, a short burst, and a frequency hop, then display spectrograms with several window lengths.

## Procedure

Use short and long STFT windows with matched and mismatched overlap. Compare localization of the burst and separation of close frequencies.

## What this should teach

The uncertainty tradeoff prevents arbitrarily fine time and frequency resolution simultaneously.

## Completion condition

You can explain why one spectrogram best shows transients while another best separates tones.

## Start or implement

```bash
./bin/learn start 15
```

If this module is scaffolded, tutor mode may review this brief but must not pretend the experiment is complete. Activate Portfolio Control batch `P15` to add the runnable MATLAB experiment, explanation, walkthrough, checks, validation, and evidence.

## AI chat prompt

Act as my hands-on DSP and radar lab mentor. Create a self-contained MATLAB mini-project titled "Use a Spectrogram to See Time-Varying Frequency". The guiding question is: "How do window duration and overlap control time-frequency visibility?" Use this experiment: Create a signal containing a steady tone, a chirp, a short burst, and a frequency hop, then display spectrograms with several window lengths. Have me perform these actions: Use short and long STFT windows with matched and mismatched overlap. Compare localization of the burst and separation of close frequencies. The main concept I must learn is: The uncertainty tradeoff prevents arbitrarily fine time and frequency resolution simultaneously. Assume I am a beginner in DSP/radar but can run and edit MATLAB scripts. Focus on physical meaning, signal flow, and visual intuition rather than MATLAB syntax or library instruction. Use seeded synthetic data, one runnable script organized into clear sections, and plots after every important processing step. Show the underlying equation or operation before using any toolbox convenience function; use base MATLAB where practical and give an optional toolbox version only when it adds real value. Include expected observations, two parameter sweeps that make the concept visually obvious, one intentionally broken case, common interpretation mistakes, and a short completion checklist. Do not turn it into homework or ask me to derive long equations before seeing the experiment.

## Files currently present

- `README.md`

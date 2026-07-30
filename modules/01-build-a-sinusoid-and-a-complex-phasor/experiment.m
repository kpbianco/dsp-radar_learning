%% P01 - Build a Sinusoid and a Complex Phasor
% Concept: a real cosine is the real-axis projection of a rotating complex phasor.
clear; close all; clc;
rng(84, "twister");

%% Baseline parameters
A = 1.0;
f0 = 5;                  % Hz
phi = pi/6;              % rad
fs = 200;                % samples/s
duration = 1.0;          % s
t = 0:1/fs:duration-1/fs;

x = A*cos(2*pi*f0*t + phi);
z = A*exp(1j*(2*pi*f0*t + phi));

figure("Name", "P01 baseline time signals");
tiledlayout(3,1);
nexttile; plot(t, x, "LineWidth", 1.3); grid on;
xlabel("Time (s)"); ylabel("x(t)"); title("Real cosine");
nexttile; plot(t, real(z), t, imag(z), "LineWidth", 1.2); grid on;
xlabel("Time (s)"); ylabel("Amplitude"); legend("I = real(z)", "Q = imag(z)");
title("Complex phasor components");
nexttile; plot(real(z), imag(z), "LineWidth", 1.3); axis equal; grid on;
xlabel("I"); ylabel("Q"); title("IQ trajectory");

max_projection_error = max(abs(x - real(z)));
fprintf("Maximum |cosine - real(phasor)| = %.3g\n", max_projection_error);

%% Positive and negative frequency rotate in opposite directions
z_positive = exp(1j*2*pi*f0*t);
z_negative = exp(-1j*2*pi*f0*t);
figure("Name", "P01 rotation direction");
tiledlayout(1,2);
nexttile; plot(real(z_positive), imag(z_positive), "LineWidth", 1.2); axis equal; grid on;
xlabel("I"); ylabel("Q"); title("Positive frequency");
nexttile; plot(real(z_negative), imag(z_negative), "LineWidth", 1.2); axis equal; grid on;
xlabel("I"); ylabel("Q"); title("Negative frequency");

%% Parameter sweep 1 - amplitude changes radius, not rotation rate
amplitudes = [0.5 1.0 1.5];
figure("Name", "P01 amplitude sweep"); hold on; grid on; axis equal;
for k = 1:numel(amplitudes)
    zk = amplitudes(k)*exp(1j*(2*pi*f0*t + phi));
    plot(real(zk), imag(zk), "DisplayName", sprintf("A = %.1f", amplitudes(k)));
end
xlabel("I"); ylabel("Q"); title("Amplitude controls phasor radius"); legend("Location", "best");

%% Parameter sweep 2 - phase changes the starting angle
phases = [0 pi/4 pi/2];
figure("Name", "P01 phase sweep"); hold on; grid on;
for k = 1:numel(phases)
    xk = A*cos(2*pi*f0*t + phases(k));
    plot(t, xk, "DisplayName", sprintf("phase = %.2f rad", phases(k)));
end
xlim([0 2/f0]); xlabel("Time (s)"); ylabel("Amplitude");
title("Phase shifts the waveform in its cycle"); legend("Location", "best");

%% Deliberately broken case - too few samples per cycle
fs_bad = 8;              % below the 10 Hz Nyquist requirement for a 5 Hz tone
t_bad = 0:1/fs_bad:duration-1/fs_bad;
x_bad = cos(2*pi*f0*t_bad + phi);
figure("Name", "P01 broken sampling case");
plot(t, x, "LineWidth", 1.1, "DisplayName", "dense reference"); hold on; grid on;
stem(t_bad, x_bad, "filled", "DisplayName", "undersampled measurements");
xlabel("Time (s)"); ylabel("Amplitude"); title("Broken case: the samples suggest the wrong oscillation");
legend("Location", "best");

%% Completion evidence
assert(max_projection_error < 1e-12, "The real cosine must equal the real part of the phasor.");
fprintf("P01 complete baseline: A=%.2f, f0=%.2f Hz, phase=%.3f rad, fs=%.1f Hz\n", A, f0, phi, fs);

# Liveness Probe Failing (Repeated Restarts, Not CrashLoopBackOff)

## Symptom
A pod restarts periodically, but unlike CrashLoopBackOff, the application logs show it was running fine right before each restart, and `kubectl describe pod` shows "Liveness probe failed" in Events.

## Likely causes
- The liveness probe's timeout or endpoint is misconfigured relative to how long the application actually takes to respond under load.
- The application occasionally hangs or deadlocks without fully crashing, and the liveness probe is correctly catching a real problem.

## Diagnosis steps
1. Run `kubectl describe pod <pod-name>` and check the exact liveness probe configuration (path, port, timeoutSeconds, periodSeconds) against what the application actually needs.
2. Correlate the timing of probe failures with application-level metrics (CPU, request latency) to distinguish a too-strict probe from a genuine application hang.

## Recommended action
If the probe is simply too strict, increase `timeoutSeconds`/`periodSeconds` or adjust `failureThreshold`. If the application is genuinely hanging, this runbook's real fix is investigating the application itself, not the probe configuration.

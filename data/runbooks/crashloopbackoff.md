# CrashLoopBackOff

## Symptom
A pod repeatedly restarts and shows status CrashLoopBackOff in `kubectl get pods`.

## Likely causes
- The application crashes immediately on startup, often due to a missing environment variable or bad config file.
- The container's entrypoint command is wrong or the binary is missing.
- The container is being OOMKilled (see oom-killed.md) which looks similar but has a different root cause.

## Diagnosis steps
1. Run `kubectl describe pod <pod-name>` and check the Events section for the real error.
2. Run `kubectl logs <pod-name> --previous` to see the logs from the last crashed instance.

## Recommended action
Fix the underlying config/env issue identified in the logs, then delete the pod so it's rescheduled: `kubectl delete pod <pod-name>`.

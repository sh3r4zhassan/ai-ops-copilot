# OOMKilled

## Symptom
`kubectl describe pod` shows the container's last state as OOMKilled, and it may be restarting repeatedly.

## Likely causes
- The container's actual memory usage exceeds its configured memory limit.
- A memory leak in the application causes usage to grow unbounded over time.

## Diagnosis steps
1. Run `kubectl top pod <pod-name>` to see current memory usage versus the limit.
2. Check `kubectl describe pod <pod-name>` for the exact configured memory limit under Containers > Limits.
3. Review application logs for signs of a leak (steadily increasing memory over hours, not a sudden spike).

## Recommended action
If usage is consistently near the limit under normal load, increase the memory limit in the deployment spec. If usage grows unbounded over time, treat it as an application bug and investigate the leak rather than just raising the limit.

# Pod Evicted Due to Node Disk Pressure

## Symptom
A pod that was previously running is suddenly gone, and `kubectl get events` shows an Eviction event mentioning "DiskPressure" around the same time.

## Likely causes
- The node's disk usage (often container image layers, logs, or ephemeral storage from pods) exceeded a threshold, triggering the kubelet's eviction manager.
- A single pod without ephemeral-storage limits consumed excessive local disk space, starving the whole node.

## Diagnosis steps
1. Run `kubectl describe node <node-name>` and check the Conditions section for `DiskPressure: True`.
2. Check actual disk usage on the node directly (`df -h`, or `du -sh /var/lib/docker` / `/var/lib/containerd` if you have node access).
3. Identify which pods lack `resources.limits.ephemeral-storage` and are the likely largest consumers.

## Recommended action
Free up disk space (prune unused images with `docker system prune` or the containerd equivalent, clear old logs), and add ephemeral-storage limits to pods to prevent a single workload from starving the node again.

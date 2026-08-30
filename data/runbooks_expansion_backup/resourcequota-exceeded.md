# Pod Fails to Schedule Due to ResourceQuota Exceeded

## Symptom
A new pod or deployment fails to create, with an error like "exceeded quota" visible in `kubectl describe` or in the deployment's Events, even though the cluster itself has available capacity.

## Likely causes
- The namespace has a ResourceQuota object limiting total CPU/memory requests or object counts, and this new workload would push the namespace over that limit.
- A teammate's workload is already consuming most of the namespace's quota, leaving no room for a new one.

## Diagnosis steps
1. Run `kubectl get resourcequota -n <namespace>` and `kubectl describe resourcequota <name> -n <namespace>` to see current usage against the limit.
2. Compare the new workload's requested resources against the remaining quota headroom.

## Recommended action
Either reduce the new workload's resource requests to fit within the existing quota, free up quota by scaling down or removing unused workloads in the namespace, or request a quota increase from whoever manages namespace policy, if that's a real option in this environment.

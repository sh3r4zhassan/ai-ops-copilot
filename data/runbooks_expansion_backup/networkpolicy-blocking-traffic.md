# NetworkPolicy Blocking Traffic

## Symptom
A pod can't reach another service in the cluster, even though both pods show Running and the target Service exists with correct endpoints.

## Likely causes
- A NetworkPolicy in the namespace restricts ingress or egress traffic and doesn't explicitly allow this pod's traffic.
- The pod's labels don't match a NetworkPolicy's expected selector, so it's unintentionally excluded from an "allow" rule.

## Diagnosis steps
1. Run `kubectl get networkpolicy -n <namespace>` to see if any policies exist in the namespace at all.
2. Run `kubectl describe networkpolicy <name> -n <namespace>` and compare its podSelector and ingress/egress rules against the actual pod labels involved.
3. Test connectivity directly with a temporary debug pod in the same namespace to confirm whether the block is policy-related or something else (DNS, service misconfiguration).

## Recommended action
Adjust the NetworkPolicy's selector or rules to explicitly allow the required traffic, or add matching labels to the pod if that's the actual intent. Avoid simply deleting the policy unless it's confirmed to be safe — it likely exists for a security reason.

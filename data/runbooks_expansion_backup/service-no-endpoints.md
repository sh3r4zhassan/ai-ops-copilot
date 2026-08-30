# Service Has No Endpoints

## Symptom
A Service exists and looks correctly configured, but any request to it fails to connect, and `kubectl get endpoints <service-name>` shows an empty or missing endpoints list.

## Likely causes
- The Service's `selector` doesn't actually match the labels on any running pod (a common typo or a label that changed on the Deployment without updating the Service).
- The pods that should be backing this Service are not actually in a Ready state (a Service only includes Ready pods as endpoints).

## Diagnosis steps
1. Run `kubectl get svc <name> -o yaml` and note the exact `spec.selector` labels.
2. Run `kubectl get pods --show-labels` and confirm at least one pod actually carries all of those labels.
3. If labels match but endpoints are still empty, check `kubectl get pods` for whether those pods are actually `Ready` (not just `Running`) — an unready pod is excluded from Service endpoints.

## Recommended action
Fix the mismatched selector/labels, or resolve whatever is preventing the backing pods from becoming Ready (often a failing readiness probe — see that runbook).

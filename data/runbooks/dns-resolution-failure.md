# DNS Resolution Failing Inside the Cluster

## Symptom
A pod can reach other pods by IP address but fails to resolve service names (e.g. `curl http://myservice` fails with a DNS error, while `curl http://<pod-ip>` works fine).

## Likely causes
- CoreDNS pods in `kube-system` are unhealthy, overloaded, or misconfigured.
- The pod's `/etc/resolv.conf` is misconfigured (rare, usually only after custom DNS policy changes).
- A NetworkPolicy is blocking traffic to CoreDNS specifically (port 53), which looks like a DNS failure but is really a networking-block issue (see the NetworkPolicy runbook).

## Diagnosis steps
1. Run `kubectl get pods -n kube-system -l k8s-app=kube-dns` and confirm CoreDNS pods are Running with no restarts.
2. From inside a debug pod, run `nslookup kubernetes.default` to test basic cluster DNS resolution directly.
3. Check CoreDNS's own logs (`kubectl logs -n kube-system <coredns-pod>`) for errors or heavy query load.

## Recommended action
Restart or scale up CoreDNS if it's unhealthy or overloaded, or fix any NetworkPolicy inadvertently blocking traffic to it. Confirm the fix with the same `nslookup` test from step 2 before considering it resolved.

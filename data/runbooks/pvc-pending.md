# PersistentVolumeClaim Stuck in Pending

## Symptom
A pod using a PersistentVolumeClaim (PVC) stays stuck in ContainerCreating, and `kubectl get pvc` shows the claim itself as Pending rather than Bound.

## Likely causes
- No StorageClass exists that satisfies the PVC's requested size/access mode, or the default StorageClass is misconfigured.
- The underlying provisioner (e.g. a cloud disk provisioner, or local-path-provisioner) failed to provision a volume.
- Insufficient capacity on the node for a local/hostPath-backed storage class.

## Diagnosis steps
1. Run `kubectl describe pvc <name> -n <namespace>` and read the Events section for the specific provisioning error.
2. Run `kubectl get storageclass` to confirm the requested StorageClass exists and is marked as the default if none was specified.
3. Check the provisioner's own pod logs (e.g. `local-path-provisioner` in `kube-system`) for errors during volume creation.

## Recommended action
Fix the StorageClass reference in the PVC spec, or resolve the provisioner's underlying error (often disk space or permissions on the node). Once corrected, delete and recreate the PVC if it doesn't reconcile automatically.

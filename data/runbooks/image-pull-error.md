# ImagePullBackOff

## Symptom
A pod is stuck in ImagePullBackOff or ErrImagePull status and never starts.

## Likely causes
- The image name or tag in the deployment spec is misspelled or doesn't exist in the registry.
- The cluster lacks credentials to pull from a private registry.

## Diagnosis steps
1. Run `kubectl describe pod <pod-name>` and check the Events section for the exact pull error message.
2. Verify the image name/tag manually: `docker pull <image>:<tag>` from a machine with registry access.
3. If it's a private registry, confirm an imagePullSecret is attached to the pod's service account.

## Recommended action
Correct the image reference in the deployment spec, or create/attach the correct imagePullSecret, then reapply the manifest.

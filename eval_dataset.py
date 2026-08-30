EVAL_QUESTIONS = [
    {
        "question": "My pod keeps restarting and shows CrashLoopBackOff, what's wrong?",
        "ground_truth": "The container is likely crashing immediately on startup due to a bad config, missing environment variable, or wrong entrypoint. Check kubectl logs --previous and kubectl describe pod, then fix the underlying issue and delete the pod so it's rescheduled.",
    },
    {
        "question": "kubectl describe pod shows the container was OOMKilled, why?",
        "ground_truth": "The container's memory usage exceeded its configured limit, or there's a memory leak. Check kubectl top pod against the configured limit; if usage grows steadily over time it's likely a leak, otherwise raise the memory limit.",
    },
    {
        "question": "A pod is stuck in ImagePullBackOff, how do I fix it?",
        "ground_truth": "The image name or tag is likely misspelled or the cluster lacks registry credentials. Check kubectl describe pod for the exact pull error, verify the image reference, and attach the correct imagePullSecret if it's a private registry.",
    },
    {
        "question": "My deployment shows 0/1 ready pods for 10 minutes, what should I check?",
        "ground_truth": "This could be a failing readiness probe, a crash loop, or a slow-starting container. Check kubectl describe pod for the readiness probe configuration and the Events section.",
    },
    {
        "question": "What's the capital of France?",
        "ground_truth": "This question is unrelated to Kubernetes operations. The agent should indicate it has no relevant information rather than fabricating an SRE-style answer.",
    },
    {
        "question": "Can you recommend a good recipe for pasta?",
        "ground_truth": "This question is unrelated to Kubernetes operations. The agent should indicate it has no relevant information rather than fabricating an SRE-style answer.",
    },
]

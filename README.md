# PodSentinel

An agentic RAG assistant that diagnoses and remediates Kubernetes cluster incidents - combining a fine-tuned LLM, a custom Go MCP server, a Kubernetes operator with a human-approval gate, and a full GitOps deployment pipeline, running end-to-end on a single home server.

**Live demo:** [podsentinel.sherazhassan.com](https://podsentinel.sherazhassan.com)
**API:** `https://api.sherazhassan.com/diagnose`

---

## What this actually does

Describe a Kubernetes problem in plain English (e.g. *"my pod is stuck in CrashLoopBackOff"*). An agent retrieves relevant internal runbooks, checks live cluster state via a custom MCP server, and returns a diagnosis. If the diagnosis calls for remediation, a Kubernetes operator can carry it out automatically - but only after a human explicitly approves it, via a simple `kubectl patch` command included in the alert.

---

## Architecture, at a glance

```
Browser (podsentinel.sherazhassan.com)
   |
   v
Cloudflare Tunnel --> Flask API (agent_server.py) --> ReAct Agent (agent.py)
   |                                                          |
   |                                            +-------------+-------------+
   |                                            v                           v
   |                                    Qdrant (RAG search)          MCP Server (Go)
   |                                                                        |
   |                                                                        v
   |                                                                Kubernetes API
   |
   +--> S3 (static frontend, proxied through Cloudflare for HTTPS)

Kubernetes Operator (Go) --> watches Incident CRs --> calls the Agent --> waits for human approval --> resolves

GitHub Actions (self-hosted runner) --> builds/tags images --> bumps Helm values.yaml --> ArgoCD auto-syncs
```

Everything runs on one Ubuntu laptop acting as a single-node k3s cluster - a deliberate constraint, not an oversight (see **Known Limitations** below).

---

## File and directory hierarchy

### Root

| Path | What it is | Why it exists |
|---|---|---|
| `agent.py` | The ReAct reasoning loop | Core agent logic: calls the LLM, parses its JSON response, invokes tools, loops until a real `final_answer` is reached. Structurally requires at least one tool call before accepting a final answer, to prevent the model from "answering" with just a stated intention. |
| `agent_server.py` | Flask API wrapping the agent | Exposes `/diagnose` over HTTP. Handles the API key check, CORS, rate limiting, basic prompt-injection input filtering, and a check against the agent leaking its own system prompt back to a caller. |
| `tools.py` | The agent's two tools | `search_runbooks` (queries Qdrant) and `get_pod_status` (queries the MCP server for live cluster state). |
| `mcp_tools.py` | MCP client wrapper | Connects `tools.py` to the Go MCP server over `streamable_http_client`. |
| `ingest.py` | RAG ingestion script | Chunks every file in `data/runbooks/`, embeds them, and loads them into Qdrant. Re-run whenever the runbook corpus changes. |
| `eval.py` / `eval_dataset.py` | Evaluation harness | Runs a fixed set of test questions through the live agent and scores the results with RAGAS (faithfulness, answer relevancy, context precision), using a separate local model as an independent judge. |
| `eval_results.csv` / `eval_results_baseline.csv` | Evaluation output | Row-level RAGAS scores - `_baseline` is the original 3-runbook/6-example setup; the unsuffixed file is the current, expanded state - kept side by side for an honest before/after comparison. |
| `requirements.txt` | Python dependencies | Includes Flask, Flask-CORS, Flask-Limiter, qdrant-client, sentence-transformers, ragas, and the `kubernetes` client library. |
| `Modelfile` | Ollama model definition | Points at the fine-tuned GGUF file and sets the system prompt used when Ollama serves `sre-copilot`. |
| `docker-compose.yml` | Local development stack | Spins up all five core services (Qdrant, Ollama, MCP server, agent, operator) together for local testing before anything touches Kubernetes. |
| `.gitignore` | Excluded paths | Keeps large/generated artifacts - virtual envs, MLflow exports, tool installers, GGUF files - out of git history. Grew several times over the course of this project after real accidental commits. |

### `data/runbooks/`
Ten Markdown files forming the RAG knowledge base - each follows a consistent **Symptom / Likely causes / Diagnosis steps / Recommended action** structure covering container crashes (CrashLoopBackOff, OOMKilled, ImagePullBackOff), networking (NetworkPolicy blocks, DNS failures, Services with no endpoints), storage (PVCs stuck Pending, node disk pressure), scheduling (ResourceQuota exceeded), and probe failures. This is the actual content the agent retrieves from - expanding it directly improves both retrieval quality and answer grounding.

### `mcp-server/`
A Go server implementing the Model Context Protocol over StreamableHTTP, giving the Python agent a stable, typed interface to live Kubernetes state (pod status, namespace listings) without embedding `client-go` calls directly into the agent's own code.

### `operator/`
A Go Kubernetes operator built with `controller-runtime`, managing a custom `Incident` resource (`crd.yaml` defines the CRD; `types.go` defines its Go structs). Watches `Incident` objects through a reconcile loop, calls the agent for a diagnosis, and - only once a human sets `spec.approved: true` - deletes the affected pod to trigger a fresh, hopefully-healthy restart. `broken-app.yaml` is a deliberately crash-looping test deployment; `incident-sample.yaml` is an example manually-created incident.

### `charts/ai-ops-copilot/`
The Helm chart deploying everything - one template per service (`agent.yaml`, `mcp-server.yaml`, `operator.yaml`, `qdrant.yaml`, `ollama.yaml`), plus RBAC. `values.yaml` holds each service's image tag, automatically bumped by CI after every build - this file changing is what ArgoCD watches for to trigger a redeploy.

### `frontend/`
`index.html` - a single-file, dependency-light chat interface. Styled as an operations console (dark theme, monospace log stream) rather than a generic chat UI, since this is genuinely an incident-response tool. Talks directly to the public API over HTTPS.

### `weekly-summary/`
A deliberately **isolated** component - its own Python script, its own Dockerfile, its own minimal read-only RBAC (`weekly-summary-rbac.yaml` in the Helm chart) - that emails a weekly cluster liveness report via a Kubernetes `CronJob` (`weekly-summary-cronjob.yaml`). Built standalone specifically so a bug here can never affect the agent or operator's already-working code.

### `.github/workflows/ci.yml`
The CI pipeline, running on a **self-hosted** GitHub Actions runner (since it needs direct access to the local k3s cluster): lints, builds and vets the Go services, builds all Docker images via Compose, tags them by commit SHA, imports them into k3s's containerd, bumps `values.yaml`, and commits the change back to `main` - which is what ArgoCD's `automated`/`selfHeal` sync policy picks up.

### `argocd-application.yaml`
The ArgoCD `Application` custom resource pointing at this repo's `charts/ai-ops-copilot` path on `main`, with automated sync and pruning enabled - the actual GitOps wiring that makes `git push` alone result in a live redeploy.

---

## Tech stack

**AI/ML:** Python, Ollama (llama.cpp), QLoRA fine-tuning (Unsloth), Qdrant, sentence-transformers, RAGAS, MLflow
**Backend:** Flask, Go (MCP server, Kubernetes operator via controller-runtime)
**Infrastructure:** Kubernetes (k3s), Docker, Helm, ArgoCD, GitHub Actions (self-hosted runner)
**Cloud/networking:** AWS S3, Cloudflare Tunnel + DNS
**Monitoring:** Kubernetes `CronJob`-based liveness alerting via email

---

## Known limitations - stated honestly, not hidden

- **CPU-only inference.** No dedicated GPU; both the agent's fine-tuned model and RAGAS's judge model run on the host laptop's CPU via Ollama, with single-request latency in the 7-11+ second range. vLLM was evaluated but not deployed for this reason - its real advantage (continuous batching) needs a GPU to matter.
- **RAGAS judge-model bias.** The evaluation harness uses a local `llama3.2:3b` as an independent judge rather than a stronger frontier model, to stay free and self-hosted - a real, named tradeoff against evaluation rigor.
- **Single point of failure.** Every component - cluster, model serving, CI runner, tunnel - runs on one physical machine. A production system would separate these concerns entirely.
- **Resource contention.** Running model inference (agent calls, evaluation runs, fine-tuning) and cluster/CI workloads simultaneously on one machine causes real, observable slowdowns - evaluation runs are best done when the system isn't otherwise in active use.

---

## Running this yourself

The full, numbered build process - from bare Ubuntu install through every step above, including every real bug hit and fixed along the way - is documented in this project's step-by-step guides, covering environment setup, the RAG pipeline, the agent loop, the MCP server, the Kubernetes operator, fine-tuning, containerization, k3s deployment, CI/CD, Helm, ArgoCD, going live, evaluation and guardrails, the weekly liveness report, and the custom domain setup.

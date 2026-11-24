# Artifacts

<!--
Deployment-ready files for this optimisation. Drop anything here that someone would need to actually apply it — don't make them reconstruct it from prose in the README.

## What belongs here

| Type | Examples |
|---|---|
| Kubernetes / OpenShift manifests | `serving-runtime.yaml`, `inference-service.yaml`, `pvc.yaml` |
| Containerfiles | `Containerfile` |
| Helm values overrides | `values-override.yaml` |
| Kustomize patches | `kustomization.yaml`, patch files |
| Scripts | install or benchmark scripts |
| Config snippets | environment variable blocks, vLLM config fragments |

-->

## Structure

- `llmInferenceService.yaml` : Baseline manifest (no KV cache offloading).
- `llmInferenceService-offload.yaml` : RHOAI ≥3.5.0 — offload via the native `spec.kvCacheOffloading` field.
- `llmInferenceService-offload-pre35.yaml` : RHOAI <3.5.0 (upstream vLLM) — same offload via `VLLM_ADDITIONAL_ARGS`.
- `build_dataset.py` : Downloads [allenai/qasper](https://huggingface.co/datasets/allenai/qasper) and the model tokenizer, and builds the interleaved benchmark dataset (not redistributed — see main `README.md#dataset`).
- `guidellm-sweep.sh` : Runs the GuideLLM concurrency sweep against a deployed model via MaaS. Requires `kvco_qasper_dataset.jsonl` (from `build_dataset.py`) alongside it.
- `results.html` : Interactive TTFT/throughput results, baseline vs. CPU-offload.

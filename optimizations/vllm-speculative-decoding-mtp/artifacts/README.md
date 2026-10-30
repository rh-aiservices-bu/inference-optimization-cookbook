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

- `llmInferenceService.yaml` : Baseline `LLMInferenceService` manifest (no speculative decoding).
- `llmInferenceService-MTP.yaml` : Same manifest with MTP (Multi-Token Prediction) speculative decoding enabled via `VLLM_ADDITIONAL_ARGS`.
- `guidellm-sweep.sh` : GuideLLM command used to benchmark each deployment (fixed concurrency sweep, 1-64).
- `results.html` : Full interactive test results - every concurrency level × every `num_speculative_tokens` value tested.
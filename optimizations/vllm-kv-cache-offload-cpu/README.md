# vllm-kv-cache-offload-cpu

![TTFT](https://img.shields.io/badge/TTFT-Improved%20(under%20pressure)-brightgreen)
![Throughput](https://img.shields.io/badge/Throughput-Improved%20(under%20pressure)-brightgreen)
![Memory](https://img.shields.io/badge/Host%20Memory-Higher-orange)
![Complexity](https://img.shields.io/badge/Complexity-Medium-yellow)

<!--
Badge colours:
  brightgreen = improved
  lightgrey   = no meaningful change
  orange      = trade-off or conditional
  red         = worse / high complexity
  yellow      = medium complexity
  green       = low complexity
-->

> ⚠️ **Trade-offs**
> - Only helps once the GPU's KV cache is under pressure (long context and/or high concurrency). 
> - Needs significantly more host (CPU) memory.

---

## What this does

The KV cache in a vLLM model deployment, is used to store the compuations of Key/Value pairs, in the GPU High Bandwidth Memory (HBM). The cache grows linearly with the LLM context, so for higher context workloads (such as RAG or Agentic), the KV cache gets very large and starts to evict stored KV pairs.

**KV cache offloading** is spilling those evicted KV pairs into a lower "tier" of storage, such as the CPU DRAM. This effectively allows the KV cache to store more, at the cost of latency when moving between the lower tier and the GPU's HBM.

Think of this as an overflow car park - you can park more cars, but the drivers need to walk further to get to the shops!

## Before / After

```
BEFORE                  HBM
                ┌─────────────────┐
                │   o    o    o   │
                │  o          o   │
   o ──────────►│        ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━► 🔥
                │  o          o   │    Discarded
                │        o        │
                │  o              │
                └─────────────────┘
                       FULL


AFTER                  HBM
                ┌─────────────────┐                       CPU RAM
                │   o    o    o   │                 ┌─────────────────┐
                │  o          o   │                 │        o        │
   o ──────────►│        ●━━━━━━━━━━━━━━━━━━━━━━━━━►│  ●           o  │
                │  o          o   │   Offloaded     │      o       o  │
                │        o        │                 │   o             │
                │  o              │                 │                 │
                └─────────────────┘                 └─────────────────┘
                       FULL
```

Without offloading, the KV pair is discarded. This means all the computation would have to happen again, if somebody asks something similar of the model.

## How to apply

See [`artifacts/`](artifacts/) for ready-to-use manifests.

The steps below explain only deploying the KV cache offload variant of the model. The ["baseline" model is also provided](./artifacts/llmInferenceService.yaml) if you want to use it as a comparison.

### Steps

1. Requires a RHOAI version with vLLM **≥ 0.22.0**. KV Cache Offloading was only made part of vLLM from that point onwards. RHOAI 3.5.0 and onwards fulfils this requirement.

2. Depending on if you're using RHOAI >=3.5.0 and the in-built vllm, or an earlier RHOAI version, with a newer upstream vLLM image, will affect how you can apply KV cache offloading.

If you're using RHOAI >=3.5.X, the LLMInferenceService CRD exposes this as it's own dedicated field. i.e.

```yaml
spec:
  kvCacheOffloading:
    cpu: "6Gi"           # size of the CPU DRAM tier
    evictionPolicy: lru  # Can be lru ("Least recently used") OR arc ("Adaptive Replacement Cache")
```

If you're using RHOAI <=3.5.0, but an upstream vLLM version, you can still apply KV Cache offloading, it just needs to be defined in the `VLLM_ADDITIONAL_ARGS` environment variable.

```yaml
spec:
  template:
    containers:
      - env:
          - name: VLLM_ADDITIONAL_ARGS
            value: '--kv-transfer-config=''{"kv_connector":"OffloadingConnector","kv_role":"kv_both","kv_connector_extra_config":{"cpu_bytes_to_use":6442450944,"eviction_policy":"lru"}}'''
```

Examples of both can be found at [`llmInferenceService-offload.yaml`](./artifacts/llmInferenceService-offload.yaml) and [`llmInferenceService-offload-pre35.yaml`](./artifacts/llmInferenceService-offload-pre35.yaml) respectively.

3. Once deployed via `LLMInferenceService`, you can confirm it's actually active by checking the pod logs for vLLM's own startup args — it will show the connector explicitly:

```
'kv_transfer_config': KVTransferConfig(kv_connector='OffloadingConnector', ..., kv_connector_extra_config={'cpu_bytes_to_use': 6442450944, 'eviction_policy': 'lru', ...})

```

4. Retrieve and build the [dataset](#dataset).

```bash
cd artifacts/
python3 build_dataset.py
# writes kvco_qasper_dataset.jsonl alongside this script (20 papers, 60 requests)
```

5. Create a MaaS subscription and generate a MaaS API key via the RHOAI UI ([docs](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/latest/html-single/govern_llm_access_with_models-as-a-service/index)).

6. Run the GuideLLM sweep against each deployed variant in turn (install `guidellm` first, e.g. `pip install guidellm`):

```bash
export GUIDELLM__MP_CONTEXT_TYPE=spawn   # required on macOS
GUIDELLM_API_KEY=sk-... ./guidellm-sweep.sh qwen25-7b-cpu-offload \
  http://maas.<cluster-domain> <namespace> "4,8,16"
```

  This writes `results_<model-name>_streams<N>.json` into the current directory — one file per concurrency level.

### Gotchas

- In testing, the `/dev/shm` sizing needed to be set higher, as setting the `spec.kvCacheoffloading.cpu` to larger than `1Gi` causes engine to crash. This needs to be set above the CPU offloading tier number. This has been done for you as part of [`llmInferenceService-offload.yaml`](./artifacts/llmInferenceService-offload.yaml).

## Test Environment

### Platform
- OpenShift 4.22.22 on AWS
- RHOAI 3.5.3

### Model Serving Details
- Model: [Qwen/Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- Runtime: vLLM 0.24.0 (**requires >=0.22.0)**
- GPU: 2x NVIDIA L4 (24GB VRAM) - 1 GPU per Model deployment

Served via RHOAI 3.5's Models-as-a-Service (MaaS); the example manifests reflect this. See the [RHOAI Documentation](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/latest/html/govern_llm_access_with_models-as-a-service/index) and the [RHOAI MaaS Guide](https://rh-aiservices-bu.github.io/rhoai-maas-guide/modules/main/index.html) for more info.

### Dataset

**This optimisation depends on reaching KV cache pressure**. Therefore, instead of using a synthetic dataset built by GuideLLM, the testing was done with a real dataset - [**allenai/qasper**](https://huggingface.co/datasets/allenai/qasper). This was then modified using the `build_dataset.py` python file, such that the questions are interleaved to simulate a realistic RAG-style pattern. 

## Test Results

Benchmarked with the [GuideLLM](https://github.com/vllm-project/guidellm) profile `concurrent` at streams = 4, 8, 16, run with [`artifacts/guidellm-sweep.sh`](artifacts/guidellm-sweep.sh). Full raw output: [`artifacts/results.html`](artifacts/results.html).

| Concurrency | Metric | Before (Baseline) | After (CPU Offload) | Delta |
|---|---|---|---|---|
| 4  | TTFT | 1,544ms | 1,571ms | +1.7% (noise — no cache pressure yet) |
| 8  | TTFT | 3,554ms | 699ms   | **-80.3% (5.1× faster)** |
| 16 | TTFT | 2,489ms | 745ms   | **-70.1% (3.3× faster)** |
| 8  | Req/s | 0.474 | 0.709 | +49.6% |
| 16 | Req/s | 0.855 | 1.078 | +26.1% |

### Test deductions

- **The benefit only appears once the GPU's KV cache is actually under pressure.** At concurrency 4, baseline and CPU-offload are within negligible difference of each other — there's no GPU KV pressure, so, nothing to evict yet, so there's nothing for offloading to save.

## Further reading

- Red Hat Developer Blog: ["Benchmarking tiered KV cache offloading with H100 GPUs on OpenShift AI 3.5"](https://developers.redhat.com/articles/2026/11/02/benchmarking-tiered-kv-cache-offloading-h100-gpus-openshift-ai-3-5)
- vLLM docs: ["KV Offloading"](https://docs.vllm.ai/en/stable/features/kv_offloading_usage/)
- [allenai/qasper dataset](https://huggingface.co/datasets/allenai/qasper)
- IBM Research paper: ["arc: A self-tuning, low overhead replacement cache"](https://research.ibm.com/publications/arc-a-self-tuning-low-overhead-replacement-cache)

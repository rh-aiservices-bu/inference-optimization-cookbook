# vllm-speculative-decoding-mtp

![TTFT](https://img.shields.io/badge/TTFT-Higher-orange)
![Throughput](https://img.shields.io/badge/Throughput-Improved-brightgreen)
![Load%20Time](https://img.shields.io/badge/Load%20Time-Unchanged-lightgrey)
![Memory](https://img.shields.io/badge/Memory-Higher-orange)
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
> - This is a throughput optimisation. TTFT will be negatively affected.
> - Speculative decoding requires tuning to get right for your workload. Keep this in mind. 

---

## What this does

Speculative decoding is a process in which you draft several tokens ahead, rather than the standard 1 token per decode cycle. The model will then verify and either accept or reject the drafted token.

Think of it as somebody jumping in to finish your sentence. You start with "I'm going to the.." and they finish with "concert tonight". Sometimes they're correct and the sentence got out quicker. Sometimes they're wrong, and you're actually going to the airport.

Multi-Token Prediction (MTP) is a specific method of speculative decoding, where the model itself includes native multi-token prediction "heads". Unlike other speculative decoding methods, this means we don't need a separate smaller "draft" model. Think of this as similar to how a smartphone can play music as well as make calls, so you don't need a separate music player.

## Before / After

```
  BEFORE: Standard Decoding                   AFTER: MTP Speculative Decoding
  (4 cycles, 1 token each)                    (1 cycle, up to 4 tokens)

                                                              ┌──► TOK 1 ✔  ─┐
                                                              │              │
  Cycle 1                                                     │              │
  ┌────────────┐                        ┌────────────┐        │              │            ┌────────────┐
  │ Big Model  │──► TOK 1               │ Big Model  │────────┼──► TOK 2 ✔   ├─ produces  │  MTP Head  │
  └────────────┘                        │  (Verify)  │        │              │            └────────────┘
                                        └────────────┘        │              │      
  Cycle 2                                                     └──► TOK 3 ✔   │      
  ┌────────────┐                                                             │      
  │ Big Model  │──► TOK 2                                                    │
  └────────────┘                                                   TOK 4 ✘  ─┘

  Cycle 3
  ┌────────────┐                        keep TOK 1-3 (confirmed), discard TOK 4,
  │ Big Model  │──► TOK 3               MTP Head drafts again starting from there
  └────────────┘

  Cycle 4
  ┌────────────┐
  │ Big Model  │──► TOK 4
  └────────────┘

  4 model passes → 4 tokens                   1 model pass → 3-4 tokens
```

Before speculative decoding, a single cycle produces 1 token. After implementing MTP speculative decoding, a single cycle involves several tokens "guesses", and in the above example, 3 of those "guessed" tokens are accepted, therefore this cycle produced 3 tokens. 

## How to apply

See [`artifacts/`](artifacts/) for ready-to-use manifests and config files.

### Steps

1. MTP speculative decoding is available only to specific models that have been trained to include it. Below is a non-exhaustive list of model families that have it enabled, but double check before assuming.

    - Gemma 4
    - Deepseek >=V3, R1
    - Qwen >=3.5

2. When serving a model with MTP, the way to enable this is via the runtime arguments. An example of this can be found in [`artifacts/llmInfereneceService-MTP.yaml`](./artifacts/llmInferenceService-MTP.yaml), but it boils down to the following `VLLM_ADDITIONAL_ARGS`:

```bash
--speculative-config=''{"method":"mtp", "num_speculative_tokens": 2}''
```

> **Note**: The ideal value of `num_speculative_tokens` is subjective to the expected workload of the model. This is explained in the [Test Results](#test-results).

3. Deploy your model via `LLMInferenceService`. In vLLM logs, you'll know it's been activated if you see the following.

```bash
[llm_base_proposer.py:1435] Detected MTP model. Sharing target model lm_head weights with the draft model.
[llm_base_proposer.py:1379] Detected MTP model. Sharing target model embedding weights with the draft model.
```

4. Once the model is Running and Ready, you inference against it like you would any other model. 

### Observability

Enabling MTP speculative decoding in vLLM causes the runtime pod to output corresponding metrics. These metrics are an additional tool that can be used to measure how effective speculative decoding is, in your environment.

> **Note**: These are specific to the runtime and version. The below is available for vLLM 0.24.0.

- `vllm:spec_decode_num_accepted_tokens_total` : The total number of tokens that the target model accepts from the draft model.
- `vllm:spec_decode_num_draft_tokens_total` : The total number of tokens created by the draft model.

Dividing the 'num accepted tokens' by the 'num draft tokens' gives you a percentage of accepted tokens. In speculative decoding, this percentage will drop as the number of drafted tokens per cycle (i.e. in the `VLLM_ADDITIONAL_ARGS`) is increased. There is a crossover point where the overhead of creating the drafted tokens outweighs the benefits of it. 

## Test Environment

### Platform
- OpenShift 4.22 on AWS
- RHOAI 3.5.2

### Model Serving Details
- [RedHatAI/Qwen3.5-9B-FP8-dynamic](https://huggingface.co/RedHatAI/Qwen3.5-9B-FP8-dynamic)
- Runtime: vLLM 0.24.0
- 1x NVIDIA L40S (46GB VRAM)

In testing, the model was served via RHOAI 3.5's Models-as-a-Service (MaaS). The example manifests reflect this. For more details, look at the [RHOAI Documentation](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/latest/html/govern_llm_access_with_models-as-a-service/index), and the [RHOAI MaaS Guide](https://rh-aiservices-bu.github.io/rhoai-maas-guide/modules/main/index.html). 

Within MaaS, the subscription was given 99,999 tokens p/s rate limit, to act as functionally infinite.

## Test Results

These results were produced with the [GuideLLM](https://github.com/vllm-project/guidellm) tool. It's a client side performance tool that will load test a model endpoint and produce metrics about the requests sent. In this instance, it was used to run against the live endpoint, sweeping two variables:

- **`num_speculative_tokens`**: baseline (disabled), then 1, 2, 3, 4, 5, 8, 10, 12, 16
- **Concurrency**: 1, 2, 4, 8, 16, 32, 48, 64 simultaneous requests

After each GuideLLM test, the model is redeployed with an updated `num_speculative_tokens` value.

The GuideLLM command used to test against the model can be found in the [guidellm-sweep.sh script](./artifacts/guidellm-sweep.sh).

Full results can be found in the [`artifacts/results.html`](./artifacts/results.html). 

The tables below give an example, where "Before" refers to the "regular" model, and the "After" is with speculative decoding enabled and 'num_speculative_tokens = 2'. This was chosen as it provides the best or near-best results.

### Test 1 - Sequential requests

| Metric | Before (Baseline) | After (MTP) | Delta |
|---|---|---|---|
| Inter-token latency | 17.7ms | 11.7ms | -34% |
| Throughput | 64.0 tok/s | 89.6 tok/s | +40% |
| Time to first token | 196.1ms | 201.0ms | +2% |

### Test 2 - 32 Concurrent requests

| Metric | Before (Baseline) | After (MTP) | Delta |
|---|---|---|---|
| Inter-token latency | 23.8ms | 17.6ms | -26% |
| Throughput | 1228.8 tok/s | 1241.6 tok/s | +1% |
| Time to first token | 445.9ms | 313.3ms | -30% |

### Test deductions

- **Inter-token latency (ITL) improves at every concurrency level tested** : This is the main benefit of speculative decoding.

- **Throughput gains shrink as concurrency rises** : With sequential requests the GPU has idle compute capacity to verify draft tokens almost for free (+40% throughput). At 32 concurrent requests the GPU is already compute-bound, so there's little spare capacity left for drafting to exploit (+1%).

- **Memory consumption increases** : The tests show GPU memory consumption raises slightly when speculative decoding is enabled. (13.18 GiB enabled vs 12.73 GiB disabled)

- **2-3 draft tokens is a sweet spot** : Generally, setting "num_speculative_tokens" to 2 or 3 is a good starting point for tuning speculative decoding to the environment.

## Further reading

- vLLM docs: ["MTP (Multi-Token Prediction)"](https://docs.vllm.ai/en/latest/features/speculative_decoding/mtp/)
- Red Hat Developer Blog: ["How speculative decoding delivers faster LLM inference"](https://developers.redhat.com/articles/2026/06/12/how-speculative-decoding-delivers-faster-llm-inference#)

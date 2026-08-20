# Quantization/INT8

## Summary

This quantization technique is [INT8](https://docs.vllm.ai/en/stable/features/quantization/llm_compressor/int8_w8a8/).

The model used to compare against the base model is [RedHatAI/phi-4-quantized.w8a8](https://huggingface.co/RedHatAI/phi-4-quantized.w8a8).

### INT W8A8 vs FP W8A8

"W8A8" generally, means to quantize both Weight and Activations to 8-bit, from (for instance) floating point 16-bit. However, the quantizing can be to both 8-bit integers _or_ 8-bit floating point. This particular repo is testing "INT8" - a quantization method generally used for older hardware, which don't have dedicated FP8 hardware acceleration cores.

Typically, compared to un-quantized models and FP W8A8 quantized models, INT8 models will have a small (1%-3%) reduction in quality / accuracy, for the 50% memory reduction and ~60% speed increases.

A deeper analysis of comparison between the two methods can be found in this [scientific paper](https://arxiv.org/abs/2303.17951).

### Supported Hardware:

- NVIDIA Compute Capability 10.0> & >7.5 (i.e. Turing, Ampere, Ada, Hopper only) 

## Deploy Quantized Model Steps

### Prerequisites

- Ensure you have the `namespace` and `gateway` deployed from the [`basemodel`](../basemodel/) directory.

### Steps

Model deployment files can be found in [artifacts](./artifacts/). 

```bash
oc apply -k ./artifacts
```

## Run the LMEvalJob

The LMEvalJob can be found in [artifacts/](./artifacts/lmevaljob.yaml). Again, this assumes that evalhub has already been setup, according to the [optimization README.md](../README.md#deploy-evalhub).

```bash
oc apply -f ./artifacts/lmevaljob.yaml
```
## Test Results

3 runs were conducted to show repeatable results. All result tables are in [artifacts](./artifacts/results.md). Below is the first run.

> **Note:** Surprisingly, all 3 runs show the exact same results, even persisting through model restarts.

| Groups |Version|Filter|n-shot|Metric| |Value | |Stderr|
|------------------|------:|------|------|------|---|-----:|---|-----:|
|mmlu | 2|none | |acc |↑ |0.7725|± |0.0053|
| - humanities | 2|none | |acc |↑ |0.7946|± |0.0107|
| - other | 2|none | |acc |↑ |0.7769|± |0.0110|
| - social sciences| 2|none | |acc |↑ |0.8542|± |0.0099|
| - stem | 2|none | |acc |↑ |0.7026|± |0.0100|

## Further Reading:

- "FP8 versus INT8 for efficient deep learning inference" - [arXiv:2303.17951](https://arxiv.org/abs/2303.17951)
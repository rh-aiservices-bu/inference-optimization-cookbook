# Quantization/<>

## Summary

This quantization technique is [INT4](https://docs.vllm.ai/en/stable/features/quantization/llm_compressor/int4/). 

The model used to compare against the base model is [RedHatAI/phi-4-quantized.w4a16](https://huggingface.co/RedHatAI/phi-4-quantized.w4a16)

### W4A16 Quantization

W4A16 quantization, means to quantize weights to 4-bit integers, whilst still maintaining the 16 bit activations. Functionally, this will reduce VRAM usage by 75% and reduces latency - while maintaining model quality and accuracy by converting the weights to 16 bit before the computations.

This quantization level is preferred in heavily bandwidth-bound, rather than compute-bound, scenarios.

### Supported Hardware:

- W4A16: [NVIDIA compute capability](https://developer.nvidia.com/cuda/gpus) >8.0.

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

| Groups |Version|Filter|n-shot|Metric| |Value | |Stderr|
|------------------|------:|------|------|------|---|-----:|---|-----:|
|mmlu | 2|none | |acc |↑ |0.7633|± |0.0053|
| - humanities | 2|none | |acc |↑ |0.7923|± |0.0108|
| - other | 2|none | |acc |↑ |0.7692|± |0.0111|
| - social sciences| 2|none | |acc |↑ |0.8450|± |0.0101|
| - stem | 2|none | |acc |↑ |0.6879|± |0.0101|
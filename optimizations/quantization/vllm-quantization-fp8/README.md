# Quantization/FP8

## Summary

This quantization technique is [FP8](https://docs.vllm.ai/en/latest/features/quantization/llm_compressor/fp8/).

This is the process of taking floating point 16 bit weights and quantizing them to floating point 8 bit weights. 

The model used to compare against the base model is [RedHatAI/phi-4-FP8-dynamic](https://huggingface.co/RedHatAI/phi-4-FP8-dynamic).

### W8A16 vs FP W8A8

FP8 quantization falls into 2 categories - Weight Only (W8A16), and Weights-And-Activations (W8A8). 

In W8A16, the weights are quantized to FP8, however the computation is still carried out in 16Bit floating point. In W8A8, both weights and activations are in FP8. This allows specialized FP8 tensor cores to be used, increasing speed in both memory loading and computation. Generally, W8A8 is quicker, however can suffer from more quality loss due resolution loss in the computation. 

This particular model we are testing is quantized to W8A8.

> Note: W8A8 _can_ also refer to INT8 quantization. See [phi-4-int8 quantization](../vllm-quantization-int8/) for more info on that.

### Supported Hardware:

- W8A16: [NVIDIA compute capability](https://developer.nvidia.com/cuda/gpus) >=7.5 (Turing onwards).
- W8A8: [NVIDIA compute capability](https://developer.nvidia.com/cuda/gpus) >= 8.9 (Ada Lovelace onwards).

## Deploy Quantized Model Steps

### Prerequisites

- Ensure you have the `namespace` and `gateway` deployed from the [`basemodel`](../basemodel/) directory.

### Steps

Model deployment files can be found in [artifacts](./artifacts/). 

```bash
oc apply -k ./artifacts
```

## Run the LMEvalJob

The LMEvalJob can be found in [artifacts/]. Again, this assumes that evalhub has already been setup, according to the [optimization README.md](../README.md#deploy-evalhub).

```bash
oc apply -f ./artifacts/lmevaljob.yaml
```
## Test Results

3 runs were conducted to show repeatable results. All result tables are in [artifacts](./artifacts/results.md). Below is the first run.

| Groups |Version|Filter|n-shot|Metric| |Value | |Stderr|
|------------------|------:|------|------|------|---|-----:|---|-----:|
|mmlu | 2|none | |acc |↑ |0.7718|± |0.0053|
| - humanities | 2|none | |acc |↑ |0.7892|± |0.0107|
| - other | 2|none | |acc |↑ |0.7746|± |0.0110|
| - social sciences| 2|none | |acc |↑ |0.8542|± |0.0099|
| - stem | 2|none | |acc |↑ |0.7058|± |0.0099|



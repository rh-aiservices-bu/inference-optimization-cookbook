# Quantization/<>

## Summary

This quantization technique is <>

The model used to compare against the base model is <>>

### explanation paragraph if needed

i.e. different types of quantization like FP8 contains W8A16 or W8A8

### Supported Hardware:

if relevant / not all hardware supports it.

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

--Markdown Table--
# Inference Optimizations

A reference collection of inference optimization techniques for vLLM and llm-d, implemented on Red Hat OpenShift AI. Answering the questions:

- What it does?
- What it benefits?
- What are the trade offs?
- How to implement it?

## Technique overview

The below table gives an overview of the optimization techniques, including their major benefit(s), trade off, complexity, and recommendation.

The complexity to implement each optimization is shown, out of:

- 🟢 - Easy
- 🟠 - Medium
- 🔴 - Hard

Recommendations are a binary pass (✅) or fail (❌). Information for why techniques are not recommended will be in their respective folders' `README.md`.

| Optimisation | Benefit | Trade-off | Complexity | Recommended
|---|---|---|---|---|
| [vLLM PyTorch Compile Cache](optimizations/vllm-pytorch-compile-cache/) |  Model Load Time | - | 🟢 | ✅
| [vLLM InstantTensor](optimizations/vllm-instanttensor-loader/) | Model Load Time | - | 🟠 | ❌ |
| [Quantization](optimizations/quantization/) | Memory footprint + Throughput | Model Quality | 🟠 | ✅ |

## Files

### Index file

The [optimization-index.csv](./optimization-index.csv) is a CSV representing a more verbose version of the table [above](./README.md#technique-overview). 

Each method has the full mapping of what it benefits, degrades, and doesn't affect. Please note, in cases where optimizations show a benefit or degredation, this classification comes from the **theory** of the method, and not necessarily what was shown in the test. 

For example, [`vllm-quantization-int8`](./optimizations/quantization/vllm-quantization-int8/) shows a degredation in "Model Quality". This is because, while [the test](./optimizations/quantization/vllm-quantization-int8/README.md#test-results) shows a _benefit_ to Model Quality, [research](https://arxiv.org/abs/2411.02355v3) suggests there is a 1-3% degredation in general.

## Other Files

- [Optimizations directory](optimizations/) : Where each optimization technique lives. An indiviudal README explaining the technique is in each directory. 
- [Templates directory](./templates/) : Contains templates to help adding optimization techniques in a standardised way.
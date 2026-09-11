# Quantization

![E2E Latency](https://img.shields.io/badge/E2E%20Latency-Improved-brightgreen)
![KV Cache Memory](https://img.shields.io/badge/KV%20Cache-Improved-brightgreen)
![Model Quality](https://img.shields.io/badge/Model%20Quality-Reduced-red)
![Complexity](https://img.shields.io/badge/Complexity-medium-yellow)

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
> - LLM "quality" can be reduced.
> - Quantization benefits differ model to model.
> - Certain methods are only available for certain hardware.

---

## What this does

Quantization is the process of taking a model's weights and shrinking them to a lower precision format i.e. 16Bit --> 8Bit. The major point of this is to reduce the memory footprint of the model, allowing for models to run in hardware constrained environments, or to allow larger models to run on smaller GPUs.

## Before / After

```
Model Weights:

     BF16  (2 bytes each)                          FP8  (1 byte each)

     ●━━━━ 0.914234 ━━━━●                          ●━━━━ 0.914 ━━━━●
     ●━━━━ 2.387100 ━━━━●                          ●━━━━ 2.387 ━━━━●
     ●━━━━ 0.004310 ━━━━●   ──── Quantize ────►    ●━━━━ 0.004 ━━━━●
     ●━━━━ 1.765400 ━━━━●                          ●━━━━ 1.765 ━━━━●
     ●━━━━ 0.482100 ━━━━●                          ●━━━━ 0.482 ━━━━●
     ●━━━━ 3.120000 ━━━━●                          ●━━━━ 3.120 ━━━━●

     16 bits · full precision                       8 bits · 50% less memory
```
- Notice how the numbers' values don't actually change too much, between the two.

- This reduction in resolution can also cause models' quality (i.e. Answer accuracy, or reasonining abilities) to drop.

## How to apply

There are many different variants of quantization, with their own pros and cons. For the sake of demonstration, each method will be separated into their own folder (i.e. [vllm-quantization-FP8](./vllm-quantization-FP8/)), with their own deployment files.

That said, each deployment will be tested against the same benchmark, to demonstrate the "quality" difference, between each method. Information on how to set this up can be found in [evalhub](./evalhub/).

### Steps

These steps are explaining how to deploy **the unquantized model** and the eval. If you don't care about running the eval, and just want files to deploy the quantized phi-4 models, go to the individual directories. i.e. [vllm-quantization-fp8](./vllm-quantization-fp8/).

#### Deploy Evalhub

Evalhub is bundled as part of RHOAI, and provides the CRDs to run Evals on your models. Information on how to deploy EvalHub is found in the [evalhub](./evalhub) folder.

#### Deploy the unquantized model

The [basemodel](./basemodel) Kustomize chart will deploy the baseline [Red Hat Validated phi-4 model](https://huggingface.co/RedHatAI/phi-4). This model is unquantized and has a tensor type of BF16, with 15B parameters.

```bash
oc apply -k basemodel/
```

This will create a gateway in the `openshift-ingress` namespace, that targets only the `model-deployment` namespace, and then deploy the model. The model is deployed unauthenticated to keep the demo simple, however this isn't recommended.

You can verify the model's inference with the below script:

```bash
ENDPOINT=$(oc get llminferenceService phi-4 -n model-deployment -o jsonpath='{.status.addresses[0].url}')
MODEL_NAME="phi-4"

curl -v -X POST "${ENDPOINT}/v1/chat/completions" \
        -H "Content-Type: application/json" \
        --data "{
                \"model\": \"${MODEL_NAME}\",
                \"messages\": [
                    {
                      \"role\": \"user\",
                      \"content\": \"Give me a 1 sentence summary about sardines.\"
                    }
                ]
        }" | jq .
```

#### Running the LMEvalJob

The last piece of the puzzle is to run the eval job itself. This comes in the form of the [LMEvalJob CR](./basemodel/lmevaljob.yaml).

```bash
oc apply -f basemodel/lmevaljob.yaml
```
This will start a pod within the `model-deployment` namespace, called `phi4-mmlu-eval`, that will run the eval and give you the results at the end.

```bash
$ oc get pod phi4-mmlu-eval -n model-deployment

NAME             READY   STATUS      RESTARTS   AGE
phi4-mmlu-eval   1/1     Running     0          2m35s

$ oc logs pod/phi4-mmlu-eval -c main -n model-deployment | tail -n 20

...
Requesting API: 8%|▊ | 1858/22800 [02:33<19:09, 18.22it/s]
Requesting API: 8%|▊ | 1861/22800 [02:33<19:11, 18.18it/s]
Requesting API: 8%|▊ | 1864/22800 [02:33<19:15, 18.12it/s]
Requesting API: 8%|▊ | 1867/22800 [02:33<19:14, 18.13it/s]
Requesting API: 8%|▊ | 1870/22800 [02:33<19:12, 18.16it/s]
Requesting API: 8%|▊ | 1873/22800 [02:34<19:10, 18.19it/s]
Requesting API: 8%|▊ | 1876/22800 [02:34<19:08, 18.21it/s]
Requesting API: 8%|▊ | 1879/22800 [02:34<19:08, 18.22it/s]
Requesting API: 8%|▊ | 1882/22800 [02:34<19:08, 18.21it/s]
Requesting API: 8%|▊ | 1885/22800 [02:34<19:03, 18.29it/s]
Requesting API: 8%|▊ | 1888/22800 [02:34<19:03, 18.28it/s]
Requesting API: 8%|▊ | 1891/22800 [02:35<19:02, 18.30it/s]
Requesting API: 8%|▊ | 1894/22800 [02:35<18:51, 18.48it/s]

```

The results will look something like this:

```bash
| Groups |Version|Filter|n-shot|Metric| |Value | |Stderr|
|------------------|------:|------|------|------|---|-----:|---|-----:|
|mmlu | 2|none | |acc |↑ |0.7723|± |0.0053|
| - humanities | 2|none | |acc |↑ |0.7946|± |0.0107|
| - other | 2|none | |acc |↑ |0.7815|± |0.0109|
| - social sciences| 2|none | |acc |↑ |0.8492|± |0.0100|
| - stem | 2|none | |acc |↑ |0.7021|± |0.0099|
```

Which looks like this rendered in markdown:

| Groups |Version|Filter|n-shot|Metric| |Value | |Stderr|
|------------------|------:|------|------|------|---|-----:|---|-----:|
|mmlu | 2|none | |acc |↑ |0.7723|± |0.0053|
| - humanities | 2|none | |acc |↑ |0.7946|± |0.0107|
| - other | 2|none | |acc |↑ |0.7815|± |0.0109|
| - social sciences| 2|none | |acc |↑ |0.8492|± |0.0100|
| - stem | 2|none | |acc |↑ |0.7021|± |0.0099|

The top "mmlu" value is what we're comparing here, so, in this case, it's 0.7723 or 77.23%.

## Test Environment

For each of the models deployed, RHOAI's Evalhub was used to run the [`mmlu`](https://arxiv.org/abs/2009.03300) benchmark. 100 samples requests from each of the 57 subjects were ran against the model, to give a representative number of the model's "quality". Depending on the model, a test run takes around 15 minutes.

Additional information on how to run the tests yourself can be found in the [evalhub directory](./evalhub).

> **Note:** This is far from an exhaustive eval of a model's quality, this is just to give a number to compare between the models. See the [Red Hat Developer blog](https://developers.redhat.com/articles/2026/05/19/evalhub-because-looks-good-me-isnt-benchmark#five_problems_that_break_ai_evaluation_at_scale) in the [appendix](#further-reading) for more complete tests.

### Platform
- OpenShift 4.19.38 on AWS
- RHOAI 3.4.2
- Model(s) served with 1x NVIDIA-L40S (Compute Capability 8.9)

## Results

### Baseline Model Results:

**Note:** 3 eval runs took place. This is just the first one. All tables are in [basemodel/results.md](./basemodel/results.md)

| Groups |Version|Filter|n-shot|Metric| |Value | |Stderr|
|------------------|------:|------|------|------|---|-----:|---|-----:|
|mmlu | 2|none | |acc |↑ |0.7721|± |0.0053|
| - humanities | 2|none | |acc |↑ |0.7946|± |0.0107|
| - other | 2|none | |acc |↑ |0.7792|± |0.0109|
| - social sciences| 2|none | |acc |↑ |0.8517|± |0.0100|
| - stem | 2|none | |acc |↑ |0.7016|± |0.0099|

### Comparison Table

> ⚠️ These numbers are just an indication of what it took to run these models in this particular test environment. For a more comprehensive comparison of LLM quantization performance trade-offs, look at [the scientific paper](https://arxiv.org/abs/2411.02355v4) referenced in the appendix.

| Models | Overall MMLU Score | GPU Memory (KV Cache) | Runtime CPU Memory* | Test Execution Time* | 
|--------|--------------------|-------------------------|-----|----|
| phi-4 | 77.21% | 27.39 GiB | 7.7 GiB | 19 mins | 
| phi-4-FP8-dynamic | 77.18% | 14.74 GiB | 3.3 GiB | 13 mins |
| phi-4-int8 | 77.25% | 14.74 GiB | 3.1 GiB | 15 mins |
| phi-4-int4 | 76.33% | 8.5 GiB | 5.2 GiB | 12 mins |

[*] : Metrics retrieved from Pod logs during runtime of the evals.

## Further reading

- [vLLM Quantization](https://docs.vllm.ai/en/latest/features/quantization/)
- [Red Hat Developer Blog: "Evalhub: Because 'looks good to me' isn't a benchmark"](https://developers.redhat.com/articles/2026/05/19/evalhub-because-looks-good-me-isnt-benchmark#five_problems_that_break_ai_evaluation_at_scale)
- [ARXIV - '"Give Me BF16 or Give Me Death"? Accuracy-Performance Trade-Offs in LLM Quantization'](https://arxiv.org/abs/2411.02355v4)
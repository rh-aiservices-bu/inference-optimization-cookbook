#!/usr/bin/env bash
# Run GuideLLM against a deployed variant, through the real MaaS gateway
# (same path a real external consumer would use), sweeping concurrency.
#
# Prerequisites:
#   - A MaaSSubscription covering the target model, and a self-service API
#     key generated the normal way:
#       curl -H "Authorization: Bearer $(oc whoami -t)" -X POST \
#         https://maas.<cluster-domain>/maas-api/v1/api-keys -d '{"name":"..."}'
#   - build_dataset.py run once to generate kvco_qasper_dataset.jsonl alongside
#     this script (the dataset itself isn't checked into this repo, only the
#     script that builds it — see ../README.md#dataset)
#   - GUIDELLM__MP_CONTEXT_TYPE=spawn set in the environment (required on macOS)
#
# Usage:
#   GUIDELLM_API_KEY=sk-... ./guidellm-sweep.sh <model-name> <gateway-url> <namespace> "4,8,16"
set -euo pipefail

MODEL="${1:?model name, e.g. qwen25-7b-cpu-offload}"
GATEWAY="${2:?MaaS gateway base URL, e.g. http://maas.apps.example.com}"
NAMESPACE="${3:?namespace the LLMInferenceService lives in}"
STREAMS="${4:-4,8,16}"

: "${GUIDELLM_API_KEY:?Set GUIDELLM_API_KEY to the self-service MaaS API key}"
export GUIDELLM__MP_CONTEXT_TYPE=spawn

TARGET="${GATEWAY}/${NAMESPACE}/${MODEL}"
DATASET="$(dirname "$0")/kvco_qasper_dataset.jsonl"

for streams in $(echo "${STREAMS}" | tr ',' ' '); do
  echo "=== ${MODEL}: concurrency=${streams} ==="
  guidellm run \
    --backend "kind=openai_http,target=${TARGET},model=${MODEL},api_key=${GUIDELLM_API_KEY}" \
    --data "kind=json_file,path=${DATASET},load_kwargs.split=train" \
    --profile "kind=concurrent,streams=${streams}" \
    --output "kind=json,path=results_${MODEL}_streams${streams}.json" \
    --disable-console-interactive
done

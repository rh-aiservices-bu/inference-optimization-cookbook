#!/usr/bin/env bash
set -euo pipefail

export GUIDELLM__MP_CONTEXT_TYPE=spawn # For MacOS

TOKEN="" # API Key from MaaS
URL="" # MaaS Endpoint
MODEL="" # MaaS Model
TOKENIZER="RedHatAI/Qwen3.5-9B-FP8-dynamic" # Model deployment

BACKEND="kind=openai_http,target=${URL},model=${MODEL},api_key=${TOKEN},validate_backend=false"
TOKENIZER_ARG="kind=huggingface_auto,model=${TOKENIZER}"

guidellm run \
  --backend "${BACKEND}" \
  --profile '{"kind":"concurrent","streams":[1,2,4,8,16,32,48,64]}' \
  --constraint "kind=max_duration,seconds=20" \
  --tokenizer "${TOKENIZER_ARG}" \
  --data "kind=synthetic_text,prompt_tokens=128,output_tokens=256" \
  --output "kind=console"

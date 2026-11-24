#!/usr/bin/env python3
"""
Build a repeated-long-document QA workload from the real QASPER dataset
(allenai/qasper, CC BY 4.0) for GuideLLM.

Rationale (see ../README.md#dataset): KV cache offloading shows benefit when the
same long prefix (a document) is revisited multiple times under enough
concurrency / working-set pressure that the GPU can't keep it resident,
forcing either prefix recomputation (no offload) or a CPU-tier restore
(offload). We build N real papers, each truncated to a target token
budget, each asked several real questions from the dataset, and interleave
the requests round-robin across documents so a document's 2nd/3rd question
arrives only after many other documents have been touched.

Output: a .jsonl file with columns "prompt" (doc + question) and
"output_tokens_count" (fixed decode length), consumable directly by
GuideLLM's `--data kind=json_file,path=...` (auto column-mapped).
"""
import argparse
import json
import random

from datasets import load_dataset
from transformers import AutoTokenizer

DOC_TOKEN_BUDGET = 5000  # truncate each paper to roughly this many tokens
QUESTIONS_PER_DOC = 3
NUM_DOCS = 20
OUTPUT_TOKENS = 150
SEED = 42

PROMPT_TEMPLATE = (
    "You are an expert research assistant. Read the following paper excerpt "
    "and answer the question concisely based only on the paper.\n\n"
    "=== PAPER: {title} ===\n{body}\n=== END PAPER ===\n\n"
    "Question: {question}\nAnswer:"
)


def flatten_full_text(example) -> str:
    paras = []
    ft = example["full_text"]
    for section, paragraphs in zip(ft["section_name"], ft["paragraphs"]):
        if section:
            paras.append(f"\n## {section}\n")
        paras.extend(paragraphs)
    return "\n".join(p for p in paras if p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="kvco_qasper_dataset.jsonl")
    ap.add_argument("--tokenizer", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--num-docs", type=int, default=NUM_DOCS)
    args = ap.parse_args()

    print("Loading tokenizer...")
    tok = AutoTokenizer.from_pretrained(args.tokenizer)

    print("Loading allenai/qasper (train split, via auto-converted parquet)...")
    ds = load_dataset(
        "parquet",
        data_files="https://huggingface.co/datasets/allenai/qasper/resolve/refs%2Fconvert%2Fparquet/qasper/train/0000.parquet",
        split="train",
    )

    random.seed(SEED)
    indices = list(range(len(ds)))
    random.shuffle(indices)

    docs = []
    for idx in indices:
        ex = ds[idx]
        qas = ex["qas"]["question"]
        if len(qas) < QUESTIONS_PER_DOC:
            continue
        body_full = flatten_full_text(ex)
        if len(body_full.split()) < 1500:  # skip very short papers
            continue

        # truncate to DOC_TOKEN_BUDGET tokens (by token count, not words)
        ids = tok(body_full, add_special_tokens=False)["input_ids"]
        if len(ids) < 2000:
            continue
        truncated_ids = ids[:DOC_TOKEN_BUDGET]
        body = tok.decode(truncated_ids)

        questions = qas[:QUESTIONS_PER_DOC]
        docs.append(
            {
                "id": ex["id"],
                "title": ex["title"],
                "body": body,
                "questions": questions,
                "doc_tokens": len(truncated_ids),
            }
        )
        if len(docs) >= args.num_docs:
            break

    print(f"Selected {len(docs)} papers.")
    for d in docs:
        print(f"  - {d['id']}: {d['title'][:60]!r} ({d['doc_tokens']} tokens)")

    # Round-robin interleave: pass 1 = Q1 of every doc, pass 2 = Q2 of every doc, ...
    rows = []
    for q_idx in range(QUESTIONS_PER_DOC):
        for d in docs:
            prompt = PROMPT_TEMPLATE.format(
                title=d["title"], body=d["body"], question=d["questions"][q_idx]
            )
            rows.append(
                {
                    "prompt": prompt,
                    "output_tokens_count": OUTPUT_TOKENS,
                    "doc_id": d["id"],
                    "pass": q_idx,
                }
            )

    with open(args.out, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    total_prompt_tokens = sum(
        len(tok(r["prompt"], add_special_tokens=False)["input_ids"]) for r in rows
    )
    print(f"Wrote {len(rows)} requests to {args.out}")
    print(f"Mean prompt tokens: {total_prompt_tokens / len(rows):.0f}")
    print(
        f"Unique document working set: ~{sum(d['doc_tokens'] for d in docs)} tokens "
        f"across {len(docs)} documents"
    )


if __name__ == "__main__":
    main()

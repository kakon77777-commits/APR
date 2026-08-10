# Hosted Semantic Inspector Smoke Test — 2026-08-10

## Outcome

The final bounded smoke test completed one OpenAI request and one Anthropic request against the
same synthetic destructive-confirmation image. Both providers produced all five required APR
facts, and the canonical values agreed 5/5.

| Provider | Model | Core score | Core agreement | Input tokens | Output tokens | Estimated USD | Latency |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| OpenAI | `gpt-5.6-luna` | 5/5 | 5/5 | 638 | 128 | $0.001406 | 3.231 s |
| Anthropic | `claude-haiku-4-5-20251001` | 5/5 | 5/5 | 1,077 | 241 | $0.002282 | 3.520 s |
| **Final run total** | | **10/10** | **5/5** | **1,715** | **369** | **$0.003688** | **6.751 s sequential** |

The five scored facts were dialog visibility, intent, object count, irreversibility, and the safe
action. APR converted each response into archived visual evidence and current world state. OpenAI
emitted five semantic facts (six evidence records including the summary); Anthropic emitted eight
facts (nine evidence records including the summary).

## Test fixture and controls

- The fixture is generated locally by `examples/run_hosted_semantic_comparison.py`: a 640×360
  pixel-font dialog reading `DELETE 42 FILES?`, `THIS CANNOT BE UNDONE`, `CANCEL`, and `DELETE`.
- Ground-truth values are held only by the local scorer and are not disclosed in the model prompt.
- The prompt supplies a multi-choice canonical label contract for intent and safe action. It does
  not identify which label is correct.
- Each selected provider receives one image and one prompt, with a 512-token output ceiling,
  60-second timeout, no tools, and no automatic retries.
- API keys are read from process environment variables at inspection time. They are not included
  in the report, evidence records, fixture, or repository.
- Fact volatility and TTL are APR configuration (`volatile=true`, `ttl=5s`), not model output.

## Corrections discovered during the experiment

1. The calibration prompt originally included the expected values. Although both providers scored
   5/5, that score was not valid evidence of visual recognition. The values were removed.
2. The first schema asked models to choose `volatile` and `ttl`. OpenAI and Anthropic selected
   different lifecycle policies for the same screen facts. Lifecycle control was removed from the
   model schema and made deterministic APR configuration.
3. With ground-truth values hidden, both providers read the pixels correctly, but one emitted
   `delete_files` while the other emitted `delete_confirmation`. A candidate-label contract was
   added so independently generated facts can be compared and merged without silently treating
   synonyms as different world states.

Across all three bounded rounds, estimated usage was $0.004304 for OpenAI and $0.006859 for
Anthropic, or $0.011163 total. Estimates use reported token counts and the public standard rates
available on the test date; provider billing records remain authoritative.

## What this does and does not establish

This establishes that the two hosted adapters authenticated, accepted the APR image/schema
requests, returned parseable structured facts, populated the evidence pipeline, and agreed on one
controlled fixture after the semantic contract was corrected.

It does **not** establish general visual accuracy, robustness to real desktops, superiority over a
full-processing baseline, calibration quality across tasks, production safety, or theorem-level
support for APR. Those require a larger blinded fixture set, repeated samples, failure cases,
baseline comparisons, and cost/latency distributions.

## Reproduce

Set `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`, then run:

```powershell
python examples/run_hosted_semantic_comparison.py `
  --provider both `
  --output artifacts/hosted-semantic-smoke.json
```

The generated fixture and JSON report are under the ignored `artifacts/` directory by default when
those paths are selected; credentials must never be placed in the repository.

Provider references used for the implementation:

- [OpenAI model catalog](https://developers.openai.com/api/docs/models)
- [OpenAI images and vision](https://developers.openai.com/api/docs/guides/images-vision)
- [Anthropic Messages API](https://platform.claude.com/docs/en/api/messages/create)
- [Anthropic vision guide](https://platform.claude.com/docs/en/build-with-claude/vision)
- [Anthropic structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

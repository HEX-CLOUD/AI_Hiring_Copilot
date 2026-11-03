# TalentIQ Synopsis Alignment

## Implemented research pipeline

- Structured PDF/DOCX candidate and job-document extraction.
- Deterministic matching baseline for comparison and recruiter transparency.
- MiniLM semantic embeddings with ChromaDB candidate retrieval.
- Retrieval-augmented candidate briefs, with optional local Phi-3 generation through Ollama.
- Per-role recruiter decisions (`shortlisted`, `interview`, `rejected`) captured as labelled outcome data.
- Supervised ranking-model dataset and training endpoints. The model trains only from recorded recruiter decisions.
- Evaluation metadata: sample count, MAE, R2 when enough labels are available, and feature importances.

## Research integrity notes

- The ranking model remains inactive until it has enough real labels. The deterministic baseline is retained for comparison.
- Initial labels represent recruiter workflow outcomes, not a claim of objective candidate quality.
- Dataset source, consent/licensing, de-identification, model limitations, fairness analysis, and evaluation outcomes must be documented in the final report.
- SHAP is a planned formal attribution layer. Current score contributions and random-forest feature importances are transparent but are not SHAP values.

## Reproducible workflow

1. Create/import candidate and job profiles.
2. Save recruiter decisions across several role-candidate pairs.
3. Inspect `GET /api/v1/ml/ranking/dataset`.
4. Train with `POST /api/v1/ml/ranking/train` once at least six labelled decisions with two outcomes exist.
5. Record `GET /api/v1/ml/ranking/status` metrics and feature importances in the project report.

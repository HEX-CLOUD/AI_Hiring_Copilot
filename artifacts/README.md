# TalentIQ AI Artifacts

This folder makes the local AI assets used during a demo easy to locate.

| Location | What it contains | Used by |
| --- | --- | --- |
| `rag_vector_store/` | ChromaDB persistence files and candidate-profile embeddings | Semantic retrieval and RAG evidence retrieval |
| `ml_models/ranking_model.joblib` | The trained scikit-learn Random Forest artifact | ML calibration comparison |

The folders above are generated locally and intentionally ignored by Git. Run
the demo seed command to recreate them when needed:

```powershell
.\venv\Scripts\python.exe scripts\seed_demo_data.py
```

The `all-MiniLM-L6-v2` embedding model and local Phi-3 model are installed in
their runtime caches (Sentence Transformers/Hugging Face and Ollama), rather
than copied into this repository.

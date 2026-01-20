# app/feedback_store.py
import os
import json
from datetime import datetime
from pathlib import Path 

PASTA_FEEDBACK = Path("feedback")
ARQ_FEEDBACK = PASTA_FEEDBACK / "feedback.jsonl"

def salvar_feedback(texto_email: str, categoria_prevista: str, categoria_correta: str):
    os.makedirs(PASTA_FEEDBACK, exist_ok=True)

    linha = {
        "data": datetime.utcnow().isoformat(),
        "texto": texto_email,
        "previsto": categoria_prevista,
        "correto": categoria_correta
    }

    with open(ARQ_FEEDBACK, "a", encoding="utf-8") as f:
        f.write(json.dumps(linha, ensure_ascii=False) + "\n")
 
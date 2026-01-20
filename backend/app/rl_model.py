import json
from datetime import datetime
from pathlib import Path
from typing import Tuple

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.sample_training_data import TREINO_EMAILS
from app.text_rules import tem_indicio_financeiro

# Pasta/arquivos de saída (fácil de entender)
PASTA_ARTIFACTS = Path("artifacts")
ARQ_PIPELINE = PASTA_ARTIFACTS / "pipeline.joblib"
ARQ_METRICAS = PASTA_ARTIFACTS / "metrics.json"
ARQ_META = PASTA_ARTIFACTS / "model_meta.json"

RANDOM_STATE = 42


def treinar_modelo() -> Pipeline:
    """Treina o classificador e salva pipeline + métricas em artifacts/."""
    PASTA_ARTIFACTS.mkdir(exist_ok=True)

    textos = [item["texto"] for item in TREINO_EMAILS]
    rotulos = [item["categoria"] for item in TREINO_EMAILS]

    # Split simples e estratificado (pra não “treinar e rezar”)
    x_treino, x_teste, y_treino, y_teste = train_test_split(
        textos,
        rotulos,
        test_size=0.2,
        stratify=rotulos,
        random_state=RANDOM_STATE,
    )

    min_df = 1 if len(textos) < 200 else 2
    pipeline = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    max_features=3000,
                    ngram_range=(1, 2),
                    min_df=min_df,

                ),
            ),
            (
                "modelo",
                LogisticRegression(
                    max_iter = 300,
                    random_state = RANDOM_STATE,
                    class_weight = "balanced"
                ),
            ),
        ]
    )

    pipeline.fit(x_treino, y_treino)

    # Avaliação mínima (salva em JSON pra mostrar maturidade)
    pred_teste = pipeline.predict(x_teste)

    relatorio = classification_report(y_teste, pred_teste, output_dict=True, zero_division=0)
    labels = list(pipeline.classes_)
    matriz = confusion_matrix(y_teste, pred_teste, labels=labels).tolist()



    metricas = {
        "criado_em": datetime.utcnow().isoformat() + "Z",
        "random_state": RANDOM_STATE,
        "tamanho_treino": len(x_treino),
        "tamanho_teste": len(x_teste),
        "labels": labels,
        "classification_report": relatorio,
        "confusion_matrix": matriz,
    }

    with open(ARQ_METRICAS, "w", encoding="utf-8") as f:
        json.dump(metricas, f, ensure_ascii=False, indent=2)

    meta = {
        "criado_em": metricas["criado_em"],
        "artefato": str(ARQ_PIPELINE),
        "max_features": 3000,
        "ngram_range": [1, 2],
        "modelo": "LogisticRegression",
        "min_df": min_df
    }
    with open(ARQ_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    joblib.dump(pipeline, ARQ_PIPELINE)
    return pipeline


def carregar_modelo() -> Pipeline:
    """Carrega pipeline treinado; se não existir, treina."""
    if not ARQ_PIPELINE.exists():
        return treinar_modelo()
    return joblib.load(ARQ_PIPELINE)


def classificar_texto(texto_email: str) -> Tuple[str, float]:
    """
    Retorna (categoria, confianca).
    - Usa predict_proba do pipeline
    - Aplica regra simples baseada em indícios financeiros
    """
    pipeline = carregar_modelo()

    texto_email = (texto_email or "").strip()

    probs = pipeline.predict_proba([texto_email])[0]
    classes = list(pipeline.classes_)

    idx_max = int(probs.argmax())
    categoria = classes[idx_max]
    confianca = float(probs[idx_max])

    # OBS: neste protótipo, "produtivo" foi definido como e-mails financeiros/documentais.
    # Logo, ausência de indício financeiro reduz o nível de confiança, sem sobrescrever a classe.
    # ≥ 0.80 → “alta confiança”
    # 0.60–0.79 → “confiança média”
    # < 0.60 → “baixa confiança”
    if not tem_indicio_financeiro(texto_email) and categoria == "produtivo":
        confianca = min(confianca, 0.79)

    return categoria, confianca

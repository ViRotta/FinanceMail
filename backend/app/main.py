# app/main.py
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from pydantic import BaseModel, field_validator

from app.rl_model import classificar_texto, carregar_modelo
from app.ai_client import validar_categoria_com_llama, gerar_resposta_com_llama
from app.feedback_store import salvar_feedback
from app.text_rules import tem_indicio_financeiro, tem_indicio_social

logger = logging.getLogger("financemail")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="FinanceMail")

frontend_origin = os.getenv("FRONTEND_ORIGIN", "").strip()

origins = ["http://localhost:5173"]
if frontend_origin:
    origins.append(frontend_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalizar_categoria(valor: str, categoria_padrao: str) -> str:

    texto = (valor or "").strip().lower()

    if "improd" in texto:
        return "improdutivo"

    if "nao produt" in texto or "não produt" in texto:
        return "improdutivo"

    if "produt" in texto:
        return "produtivo"

    return categoria_padrao




class EmailEntrada(BaseModel):
    texto: str

    @field_validator("texto")
    @classmethod
    def validar_texto(cls, v: str):
        v = (v or "").strip()
        if not v:
            raise ValueError("texto não pode ser vazio")
        return v


class FeedbackEntrada(BaseModel):
    texto: str
    previsto: str
    correto: str

    @field_validator("previsto", "correto")
    @classmethod
    def validar_categoria(cls, v: str):
        v = (v or "").strip().lower()
        if v not in {"produtivo", "improdutivo"}:
            raise ValueError("categoria deve ser 'produtivo' ou 'improdutivo'")
        return v

    @field_validator("texto")
    @classmethod
    def validar_texto_feedback(cls, v: str):
        v = (v or "").strip()
        if not v:
            raise ValueError("texto não pode ser vazio")
        return v



@app.on_event("startup")
def aquecer_modelo():
    # evita "primeira chamada lenta" em deploy
    try:
        carregar_modelo()
        logger.info("Modelo aquecido com sucesso.")
    except Exception:
        # não derruba a API no boot, mas deixa rastreável
        logger.exception("Falha ao aquecer o modelo no startup.")



@app.get("/")
def home():
    return {
        "message": "API FinanceMail no ar 🚀",
        "docs": "/docs",
        "status": "/status",
    }


@app.get("/status")
def status():
    return {"status": "ok"}


@app.post("/classificar")
def classificar_email(dados: EmailEntrada):
    texto_email = (dados.texto or "").strip()

    # 1) Resultado do modelo local (já inclui as regras do rl_model.py)
    categoria_modelo, confianca_modelo = classificar_texto(texto_email)

    categoria_final = categoria_modelo
    confianca_final = float(confianca_modelo)

    consultou_llama = False
    mudou_por_llama = False

     # 2) regra "anti-erro feio": se for social e NÃO tiver indício financeiro, é improdutivo.
    # Isso evita o LLaMA inventar "produtivo" em mensagens tipo "Feliz natal".
    if tem_indicio_social(texto_email) and not tem_indicio_financeiro(texto_email):
        categoria_final = "improdutivo"
        confianca_final = max(confianca_final, 0.80)  # aqui você pode ser mais confiante
    else:
        # 3) segunda opinião do LLaMA só quando a confiança do modelo for baixa
        if confianca_modelo < 0.65:
            consultou_llama = True
            try:
                categoria_llama_raw = validar_categoria_com_llama(texto_email)
                categoria_llama = normalizar_categoria(
                    categoria_llama_raw, padrao=categoria_modelo
                )

                # não deixa o LLaMA contradizer regra de indício financeiro
                # (se tem indício financeiro forte, não deixa virar improdutivo)
                if tem_indicio_financeiro(texto_email) and categoria_llama == "improdutivo":
                    categoria_llama = categoria_modelo

                if categoria_llama != categoria_modelo:
                    mudou_por_llama = True
                    categoria_final = categoria_llama
                    confianca_final = 0.65  # conservador, não inventa super confiança

            except Exception:
                logger.exception("Falha ao consultar LLaMA para validação de categoria.")
                consultou_llama = False
                mudou_por_llama = False
 

    # 4) Geração de resposta (com fallback)
    try:
        resposta = gerar_resposta_com_llama(texto_email, categoria_final)
    except Exception:
        logger.exception("Falha ao gerar resposta com LLaMA.")
        if categoria_final == "produtivo":
            resposta = (
                "Prezado(a),\n\n"
                "Recebido. Vou encaminhar para análise e providências.\n\n"
                "Atenciosamente."
            )
        else:
            resposta = (
                "Olá!\n\n"
                "Obrigado pela mensagem.\n\n"
                "Atenciosamente."
            )
    # Fonte mais honesta/auditável
    if mudou_por_llama:
        fonte = "llama"
    elif consultou_llama:
        fonte = "modelo+llama"
    else:
        fonte = "modelo"

    return {
        "categoria": categoria_final,
        "confianca": round(float(confianca_final), 2),
        "fonte": fonte,
        "resposta": resposta,
        "categoria_modelo": categoria_modelo,
        "confianca_modelo": round(float(confianca_modelo), 2),
    }


@app.post("/feedback")
def feedback(dados: FeedbackEntrada):
    salvar_feedback(
        texto_email=(dados.texto or "").strip(),
        categoria_prevista=dados.previsto,
        categoria_correta=dados.correto,
    )
    return {"ok": True}


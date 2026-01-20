# app/ai_client.py
import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

MODELO_LLAMA = "meta-llama/Meta-Llama-3-8B-Instruct"

def _get_client():
    token = os.getenv("HF_TOKEN")
    if not token:
        return None, "Erro: HF_TOKEN não encontrado no .env"
    return InferenceClient(api_key=token), None

def _normalizar_resposta_categoria(texto: str) -> str:
    """
    Garante que a saída seja exatamente 'produtivo' ou 'improdutivo'.
    Se vier algo estranho, retorna 'improdutivo' por segurança.
    """
    saida = (texto or "").strip().lower()

    # prioridade para improdutivo (evita o bug improdutivo -> produtivo)
    if "improdutivo" in saida:
        return "improdutivo"

    # se responder só "produtivo"
    if "produtivo" in saida:
        return "produtivo"

    return "improdutivo"

def validar_categoria_com_llama(texto_email: str) -> str:
    client, erro = _get_client()
    if erro:
        return "improdutivo"

    prompt = f"""
Você vai classificar um email em APENAS uma categoria:
- produtivo = tem cobrança, boleto, nota fiscal, DANFE, pagamento, pix, vencimento, valor, CNPJ, fatura, duplicata.
- improdutivo = felicitações, agradecimentos gerais, conversa, sem ação financeira.

Responda somente com UMA palavra: produtivo ou improdutivo.

EMAIL:
{texto_email}
""".strip()

    resp = client.chat.completions.create(
        model=MODELO_LLAMA,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10,
        temperature=0.0,
    )

    texto_resposta = resp.choices[0].message.content
    return _normalizar_resposta_categoria(texto_resposta)

def gerar_resposta_com_llama(texto_email: str, categoria: str) -> str:
    client, erro = _get_client()
    if erro:
        return erro

    if categoria == "produtivo":
        instrucao = "Escreva uma resposta curta confirmando recebimento e dizendo que o financeiro vai analisar/processar. Seja educado e objetivo."
    else:
        instrucao = "Escreva uma resposta curta e educada, sem prometer ação financeira, apenas agradecendo."

    prompt = f"""
{instrucao}

EMAIL:
{texto_email}
""".strip()

    resp = client.chat.completions.create(
        model=MODELO_LLAMA,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=160,
        temperature=0.2,
    )

    return resp.choices[0].message.content.strip()

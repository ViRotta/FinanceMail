import re
import unicodedata

PALAVRAS_FINANCEIRAS_FORTES = [
    "boleto", "linha digitavel", "codigo de barras",
    "danfe", "nota fiscal", "nfe", "nf-e",
    "fatura", "cobranca", "pagamento", "duplicata",
    "cnpj", "fornecedor", "remessa"
]

PALAVRAS_FINANCEIRAS_FRACAS = [
    "pix", "chave pix", "vencimento", "valor", "banco"
]

PALAVRAS_SOCIAIS = [
    "feliz natal", "feliz ano novo", "bom dia", "boa tarde", "boa noite",
    "obrigado", "obrigada", "agradeco", "parabens"
]

# Regex simples (bem “MVP”)
REGEX_CNPJ = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")
REGEX_LINHA_DIGITAVEL = re.compile(r"\b(\d[\d\s\.\-]{40,60}\d)\b")  # bem permissivo
REGEX_DINHEIRO = re.compile(r"\b(r\$)\s*\d{1,3}(\.\d{3})*(,\d{2})?\b")


def _tirar_acentos(texto: str) -> str:
    texto = texto or ""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )

def normalizar(texto: str) -> str:
    texto = _tirar_acentos(texto).lower()
    texto = " ".join(texto.split())
    return texto


def score_financeiro(texto_email: str) -> int:
    texto = normalizar(texto_email)
    score = 0

    # Palavras fortes valem mais
    for palavra in PALAVRAS_FINANCEIRAS_FORTES:
        if palavra in texto:
            score += 2

    # Palavras fracas valem pouco (evita falso positivo)
    for palavra in PALAVRAS_FINANCEIRAS_FRACAS:
        if palavra in texto:
            score += 1

    # Padrões (quando aparecem, é um sinal forte)
    if REGEX_CNPJ.search(texto):
        score += 2
    if REGEX_LINHA_DIGITAVEL.search(texto):
        score += 2
    if REGEX_DINHEIRO.search(texto):
        score += 1

    return score


def tem_indicio_financeiro(texto_email: str) -> bool:
    # limiar simples (ajuste fino depois)
    return score_financeiro(texto_email) >= 2


def tem_indicio_social(texto_email: str) -> bool:
    texto = normalizar(texto_email)
    return any(palavra in texto for palavra in PALAVRAS_SOCIAIS)

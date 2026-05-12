# %% Imports
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
import re
import unicodedata

nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

STOPWORDS = set(stopwords.words("portuguese"))
STOPWORDS.update(["app", "banco", "muito", "mais", "ser", "ter", "estar"])

# %% Classificação de sentimento

PALAVRAS_POSITIVAS = {
    "excelente", "ótimo", "otimo", "rapido", "rápido", "eficiente",
    "satisfeito", "parabéns", "parabens", "ágil", "agil", "facil",
    "fácil", "melhorou", "resolveu", "aprovado", "atencioso",
    "educado", "qualidade", "recomendo", "impressionado"
}

PALAVRAS_NEGATIVAS = {
    "péssimo", "pessimo", "horrivel", "horrível", "ruim", "absurdo",
    "cobrança", "cobranca", "indevida", "falhando", "falhou", "sumiu",
    "grosseiro", "abusiva", "impossível", "impossivel", "terrível",
    "terrivel", "problema", "cancelei", "travou", "semanas", "horas"
}

def classificar_sentimento(texto: str) -> str:
    if not texto or not isinstance(texto, str):
        return "neutro"
    texto_norm = unicodedata.normalize("NFKD", texto.lower())
    texto_norm = "".join(c for c in texto_norm if not unicodedata.combining(c))
    palavras = set(texto_norm.split())
    pos = len(palavras & PALAVRAS_POSITIVAS)
    neg = len(palavras & PALAVRAS_NEGATIVAS)
    if pos > neg:
        return "positivo"
    elif neg > pos:
        return "negativo"
    return "neutro"

# %% Classificação NPS

def classificar_nps(score: int) -> str:
    if score >= 9:
        return "promotor"
    elif score >= 7:
        return "neutro"
    return "detrator"

# %% Extração de temas

def extrair_temas(textos: list[str], top_n: int = 10) -> list[dict]:
    todos_tokens = []
    for texto in textos:
        if not isinstance(texto, str):
            continue
        texto_norm = unicodedata.normalize("NFKD", texto.lower())
        texto_norm = "".join(c for c in texto_norm if not unicodedata.combining(c))
        texto_norm = re.sub(r"[^a-z\s]", " ", texto_norm)
        tokens = word_tokenize(texto_norm, language="portuguese")
        tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 3]
        todos_tokens.extend(tokens)
    counter = Counter(todos_tokens)
    return [{"tema": k, "frequencia": v} for k, v in counter.most_common(top_n)]

# %% Pipeline completo

def analisar_csat(df: pd.DataFrame) -> dict:
    """
    Pipeline completo de análise CSAT/NPS.
    Entrada: DataFrame com colunas comentario, nps_score, canal, produto
    Saída: dict com métricas, sentimentos, temas e NPS
    """
    # Sentimento
    df["sentimento"] = df["comentario"].apply(classificar_sentimento)

    # Classificação NPS
    df["nps_categoria"] = df["nps_score"].apply(classificar_nps)

    # Cálculo NPS
    total = len(df)
    promotores   = (df["nps_categoria"] == "promotor").sum()
    detratores   = (df["nps_categoria"] == "detrator").sum()
    nps_score    = round(((promotores - detratores) / total) * 100, 1)

    # Temas por sentimento
    negativos = df[df["sentimento"] == "negativo"]["comentario"].tolist()
    positivos = df[df["sentimento"] == "positivo"]["comentario"].tolist()

    # Distribuição por canal
    por_canal = df.groupby("canal")["nps_score"].mean().round(1).to_dict()

    # Distribuição por produto
    por_produto = df.groupby("produto")["nps_score"].mean().round(1).to_dict()

    return {
        "resumo": {
            "total_registros":  total,
            "nps_score":        nps_score,
            "promotores":       int(promotores),
            "neutros":          int((df["nps_categoria"] == "neutro").sum()),
            "detratores":       int(detratores),
            "pct_promotores":   round(promotores / total * 100, 1),
            "pct_detratores":   round(detratores / total * 100, 1),
        },
        "sentimentos": {
            "positivo": int((df["sentimento"] == "positivo").sum()),
            "neutro":   int((df["sentimento"] == "neutro").sum()),
            "negativo": int((df["sentimento"] == "negativo").sum()),
        },
        "temas_insatisfacao": extrair_temas(negativos, top_n=10),
        "temas_satisfacao":   extrair_temas(positivos, top_n=10),
        "por_canal":          por_canal,
        "por_produto":        por_produto,
        "amostra_detratores": df[df["nps_categoria"] == "detrator"][
            ["cliente", "comentario", "nps_score", "canal"]
        ].head(5).to_dict(orient="records"),
    }

# %% Teste rápido
if __name__ == "__main__":
    df = pd.read_csv("data/csat_feedback.csv")
    resultado = analisar_csat(df)

    print(f"\n{'='*45}")
    print(f"NPS SCORE: {resultado['resumo']['nps_score']}")
    print(f"{'='*45}")
    print(f"Promotores: {resultado['resumo']['promotores']} ({resultado['resumo']['pct_promotores']}%)")
    print(f"Detratores: {resultado['resumo']['detratores']} ({resultado['resumo']['pct_detratores']}%)")
    print(f"\nSentimentos: {resultado['sentimentos']}")
    print(f"\nTop temas de insatisfação:")
    for t in resultado['temas_insatisfacao'][:5]:
        print(f"  {t['tema']}: {t['frequencia']}x")
    print(f"\nNPS por canal:")
    for canal, score in resultado['por_canal'].items():
        print(f"  {canal}: {score}")
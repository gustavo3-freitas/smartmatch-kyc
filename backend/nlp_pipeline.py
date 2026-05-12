# %% Imports
import unicodedata
import re
import nltk
import spacy
from nltk.corpus import stopwords as nltk_stopwords

# Baixa recursos NLTK necessários
nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)
nltk.download("rslp", quiet=True)  # Stemmer português

# Carrega modelos spaCy
nlp_pt = spacy.load("pt_core_news_sm")
nlp_en = spacy.load("en_core_web_sm")

# %% Stopwords combinadas (NLTK + conectivos de nomes)

STOPWORDS_PT = set(nltk_stopwords.words("portuguese"))
STOPWORDS_EN = set(nltk_stopwords.words("english"))

CONECTIVOS_NOMES = {
    "de", "da", "do", "dos", "das", "e", "van", "von",
    "del", "della", "di", "du", "le", "la", "los", "las"
}

PREFIXOS_TITULOS = {
    "sr", "sra", "dr", "dra", "mr", "mrs", "ms", "prof",
    "jr", "neto", "filho", "ing", "dipl", "mba"
}

# %% Detecção de idioma (simples por país)

def detectar_idioma(country: str) -> str:
    return "pt" if country == "BR" else "en"

# %% Normalização base

def remover_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def normalizar_base(texto: str) -> str:
    """Limpeza inicial antes do NLP."""
    if not texto or not isinstance(texto, str):
        return ""
    texto = texto.lower().strip()
    texto = remover_acentos(texto)
    # Remove pontuação exceto espaço
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    # Remove espaços duplos
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

# %% Pipeline NLP com spaCy

def extrair_tokens_spacy(texto: str, idioma: str = "en") -> list[str]:
    """
    Tokeniza e lematiza com spaCy.
    Remove stopwords, títulos e tokens muito curtos.
    """
    modelo = nlp_pt if idioma == "pt" else nlp_en
    doc = modelo(texto)

    tokens = []
    for token in doc:
        t = token.lemma_.lower().strip()
        # Filtra stopwords, títulos, pontuação e tokens curtos
        if (
            not token.is_stop
            and not token.is_punct
            and not token.is_space
            and t not in CONECTIVOS_NOMES
            and t not in PREFIXOS_TITULOS
            and len(t) > 1
        ):
            tokens.append(t)
    return tokens

# %% Pipeline NLTK (stemming para PT)

def extrair_tokens_nltk(texto: str, idioma: str = "pt") -> list[str]:
    """
    Tokeniza com NLTK e aplica stemming para português.
    Útil como fallback ou comparação com spaCy.
    """
    from nltk.stem import RSLPStemmer
    from nltk.tokenize import word_tokenize

    stemmer = RSLPStemmer()
    stopwords = STOPWORDS_PT if idioma == "pt" else STOPWORDS_EN

    tokens = word_tokenize(texto, language="portuguese" if idioma == "pt" else "english")
    tokens = [
        stemmer.stem(t) for t in tokens
        if t.isalpha()
        and t not in stopwords
        and t not in CONECTIVOS_NOMES
        and t not in PREFIXOS_TITULOS
        and len(t) > 1
    ]
    return tokens

# %% Pipeline completo de preprocessamento

def preprocessar(nome: str, country: str = "US") -> str:
    """
    Pipeline completo: normalização + spaCy NLP.
    Entrada:  'Dr. João da Silva Santos'  (country='BR')
    Saída:    'joao silva santos'
    """
    idioma = detectar_idioma(country)
    texto = normalizar_base(nome)
    tokens = extrair_tokens_spacy(texto, idioma)

    # Fallback: se spaCy não retornou tokens, usa texto normalizado
    if not tokens:
        return texto

    return " ".join(tokens)

def preprocessar_lote(nomes: list[dict]) -> list[dict]:
    """
    Processa uma lista de registros com campos 'name' e 'country'.
    Retorna os mesmos registros com campo 'name_processed' adicionado.
    """
    resultado = []
    for registro in nomes:
        resultado.append({
            **registro,
            "name_processed": preprocessar(
                registro.get("name", ""),
                registro.get("country", "US")
            )
        })
    return resultado

# %% Teste — roda essa célula

import pandas as pd

casos = [
    {"name": "Dr. João da Silva Santos",      "country": "BR"},
    {"name": "Joao Silva Santos",             "country": "BR"},
    {"name": "João S. Santos",                "country": "BR"},
    {"name": "JOÃO DA SILVA SANTOS",          "country": "BR"},
    {"name": "Olívia Azevedo",               "country": "BR"},
    {"name": "Olivia Azevedo",               "country": "BR"},
    {"name": "Mr. John van der Berg",         "country": "US"},
    {"name": "John Van Der Berg",             "country": "US"},
    {"name": "Lauren-Jackson",               "country": "US"},
    {"name": "Lauren Jacson",                "country": "US"},
    {"name": "Dipl.-Ing. Hans-Erich Schäfer", "country": "DE"},
]

resultados = preprocessar_lote(casos)
df_teste = pd.DataFrame(resultados)[["name", "country", "name_processed"]]
print(df_teste.to_string(index=False))

# %% Teste com dataset real
df = pd.read_csv("data/customers.csv")
print(f"\nDataset: {len(df)} registros")

# Processa amostra de 10 registros
amostra = df.head(10)[["name", "country"]].to_dict("records")
processados = preprocessar_lote(amostra)

print(f"\n{'ORIGINAL':<40} {'PAÍS':<5} {'PROCESSADO'}")
print("-" * 75)
for r in processados:
    print(f"{r['name']:<40} {r['country']:<5} {r['name_processed']}")
    

    
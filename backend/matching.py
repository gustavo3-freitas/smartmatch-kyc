# %% Imports
import pandas as pd
from Levenshtein import ratio, distance
from itertools import combinations
from nlp_pipeline import preprocessar

# %% Blocking — reduz comparações de O(n²) para O(k)

def gerar_blocking_key(nome_processado: str) -> str:
    """
    Chave de blocking: primeiras 4 letras do primeiro token.
    Agrupa nomes parecidos antes do matching — evita comparar tudo com tudo.
    
    Exemplo:
      'joao silva santo' → 'joao'
      'john smith'       → 'john'
    """
    tokens = nome_processado.strip().split()
    if not tokens:
        return "UNKNOWN"
    return tokens[0][:4].upper()

def gerar_blocking_key_secundaria(nome_processado: str) -> str:
    """
    Chave secundária: primeiras 3 letras do último token.
    Usada para casos onde o primeiro nome foi abreviado.
    
    Exemplo:
      'j silva santo' → 'SAN'
    """
    tokens = nome_processado.strip().split()
    if not tokens:
        return "UNKNOWN"
    return tokens[-1][:3].upper()

def criar_blocos(registros: list[dict]) -> dict:
    """
    Agrupa registros por blocking key.
    Cada bloco contém candidatos a duplicata.
    """
    blocos = {}
    for r in registros:
        # Blocking primário
        key1 = gerar_blocking_key(r["name_processed"])
        blocos.setdefault(key1, []).append(r)

        # Blocking secundário — captura abreviações de primeiro nome
        key2 = "SEC_" + gerar_blocking_key_secundaria(r["name_processed"])
        if key2 not in blocos:
            blocos[key2] = []
        # Só adiciona se primeiro token é curto (abreviação)
        tokens = r["name_processed"].split()
        if tokens and len(tokens[0]) <= 2:
            blocos[key2].append(r)

    return blocos

# %% Matching com Levenshtein

def calcular_similaridade(nome_a: str, nome_b: str) -> float:
    """
    Calcula similaridade entre dois nomes processados.
    Usa ratio do Levenshtein: 0.0 (nada similar) a 1.0 (idêntico).
    """
    if not nome_a or not nome_b:
        return 0.0
    return ratio(nome_a, nome_b)

def encontrar_duplicatas(
    registros: list[dict],
    threshold: float = 0.82,
    max_matches: int = 5000
) -> list[dict]:
    """
    Pipeline completo de deduplicação:
    1. Cria blocos (blocking)
    2. Compara pares dentro de cada bloco (Levenshtein)
    3. Retorna matches acima do threshold

    Args:
        registros:   lista de dicts com id, name, name_processed, country, document
        threshold:   similaridade mínima para considerar duplicata (0.0 a 1.0)
        max_matches: limite de resultados para não explodir memória

    Returns:
        lista de matches ordenada por score descendente
    """
    blocos = criar_blocos(registros)
    
    matches = []
    pares_vistos = set()
    total_comparacoes = 0

    for key, bloco in blocos.items():
        if len(bloco) < 2:
            continue

        for r_a, r_b in combinations(bloco, 2):
            # Evita comparar o mesmo par duas vezes
            par_id = tuple(sorted([r_a["id"], r_b["id"]]))
            if par_id in pares_vistos:
                continue
            pares_vistos.add(par_id)
            total_comparacoes += 1

            score = calcular_similaridade(
                r_a["name_processed"],
                r_b["name_processed"]
            )

            if score >= threshold:
                matches.append({
                    "id_a":       r_a["id"],
                    "name_a":     r_a["name"],
                    "processed_a": r_a["name_processed"],
                    "id_b":       r_b["id"],
                    "name_b":     r_b["name"],
                    "processed_b": r_b["name_processed"],
                    "score":      round(score, 4),
                    "country":    r_a.get("country", ""),
                    "document":   r_a.get("document", ""),
                })

            if len(matches) >= max_matches:
                break

    matches_ordenados = sorted(matches, key=lambda x: x["score"], reverse=True)
    
    print(f"  Blocos criados:      {len(blocos):,}")
    print(f"  Pares comparados:    {total_comparacoes:,}")
    print(f"  Matches encontrados: {len(matches_ordenados):,}")
    
    return matches_ordenados

# %% Métricas de avaliação

def avaliar_pipeline(df_original: pd.DataFrame, matches: list[dict]) -> dict:
    """
    Avalia qualidade do pipeline usando o ground truth do dataset.
    Calcula Precision, Recall e F1.
    """
    # Ground truth: pares que realmente são duplicatas
    pares_reais = set()
    grupos = df_original[df_original["is_duplicate"] == 1].groupby("cluster_id")
    for _, grupo in grupos:
        ids = grupo["id"].tolist()
        for par in combinations(ids, 2):
            pares_reais.add(tuple(sorted(par)))

    # Pares encontrados pelo pipeline
    pares_encontrados = set()
    for m in matches:
        pares_encontrados.add(tuple(sorted([m["id_a"], m["id_b"]])))

    # Métricas
    verdadeiros_positivos = len(pares_reais & pares_encontrados)
    falsos_positivos = len(pares_encontrados - pares_reais)
    falsos_negativos = len(pares_reais - pares_encontrados)

    precision = verdadeiros_positivos / max(len(pares_encontrados), 1)
    recall    = verdadeiros_positivos / max(len(pares_reais), 1)
    f1        = 2 * precision * recall / max(precision + recall, 0.001)

    return {
        "pares_reais":           len(pares_reais),
        "pares_encontrados":     len(pares_encontrados),
        "verdadeiros_positivos": verdadeiros_positivos,
        "falsos_positivos":      falsos_positivos,
        "falsos_negativos":      falsos_negativos,
        "precision":             round(precision, 4),
        "recall":                round(recall, 4),
        "f1_score":              round(f1, 4),
    }

# %% Teste com dataset real — roda essa célula

df = pd.read_csv("data/customers.csv")

print("Preprocessando nomes...")
registros = []
for _, row in df.iterrows():
    registros.append({
        "id":             int(row["id"]),
        "name":           row["name"],
        "name_processed": preprocessar(row["name"], row["country"]),
        "country":        row["country"],
        "document":       row["document"],
        "cluster_id":     int(row["cluster_id"]),
        "is_duplicate":   int(row["is_duplicate"]),
    })

print(f"Registros processados: {len(registros):,}")
print("\nRodando matching engine...")
matches = encontrar_duplicatas(registros, threshold=0.82)

# %% Avaliação — roda essa célula depois do matching

metricas = avaliar_pipeline(df, matches)

print("\n" + "="*45)
print("MÉTRICAS DO PIPELINE")
print("="*45)
print(f"Pares reais (ground truth): {metricas['pares_reais']:,}")
print(f"Pares encontrados:          {metricas['pares_encontrados']:,}")
print(f"Verdadeiros positivos:      {metricas['verdadeiros_positivos']:,}")
print(f"Falsos positivos:           {metricas['falsos_positivos']:,}")
print(f"Falsos negativos:           {metricas['falsos_negativos']:,}")
print(f"\nPrecision:  {metricas['precision']:.2%}")
print(f"Recall:     {metricas['recall']:.2%}")
print(f"F1 Score:   {metricas['f1_score']:.2%}")

# %% Amostra dos matches — top 15

print("\nTop 15 matches encontrados:")
print(f"{'Nome A':<35} {'Nome B':<35} {'Score'}")
print("-" * 78)
for m in matches[:15]:
    print(f"{m['name_a']:<35} {m['name_b']:<35} {m['score']:.2%}")
import pandas as pd
import random
import string
import unicodedata
import re
from faker import Faker

random.seed(42)
fake_br = Faker("pt_BR")
fake_us = Faker("en_US")
fake_gb = Faker("en_GB")
fake_de = Faker("de_DE")
fake_es = Faker("es_ES")
Faker.seed(42)

# ─── Tipos de ruído ───────────────────────────────────────────────────────────

def remover_acento(texto):
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def abreviar_meio(nome):
    partes = nome.split()
    if len(partes) < 3:
        return nome
    meio = [p[0] + "." for p in partes[1:-1]]
    return " ".join([partes[0]] + meio + [partes[-1]])

def abreviar_primeiro(nome):
    partes = nome.split()
    if len(partes) < 2:
        return nome
    return partes[0][0] + ". " + " ".join(partes[1:])

def remover_ultimo(nome):
    partes = nome.split()
    return " ".join(partes[:-1]) if len(partes) > 2 else nome

def remover_segundo(nome):
    partes = nome.split()
    if len(partes) < 3:
        return nome
    return partes[0] + " " + partes[-1]

def erro_digitacao(nome):
    """Troca, insere ou remove um caractere aleatório."""
    if len(nome) < 4:
        return nome
    chars = list(nome)
    op = random.choice(["troca", "insere", "remove", "transpoe"])
    idx = random.randint(1, len(chars) - 2)
    if op == "troca":
        chars[idx] = random.choice(string.ascii_lowercase)
    elif op == "insere":
        chars.insert(idx, random.choice(string.ascii_lowercase))
    elif op == "remove":
        chars.pop(idx)
    elif op == "transpoe" and idx < len(chars) - 1:
        chars[idx], chars[idx+1] = chars[idx+1], chars[idx]
    return "".join(chars)

def maiusculas(nome):
    return nome.upper()

def minusculas(nome):
    return nome.lower()

def titulo_errado(nome):
    # Capitaliza aleatoriamente
    return " ".join(
        w.capitalize() if random.random() > 0.3 else w.lower()
        for w in nome.split()
    )

def prefixo_errado(nome):
    prefixos = ["Mr. ", "Mrs. ", "Dr. ", "Sr. ", "Sra. ", "Prof. "]
    return random.choice(prefixos) + nome

def sufixo_errado(nome):
    sufixos = [" Jr.", " Jr", " Filho", " Neto", " II", " III"]
    return nome + random.choice(sufixos)

def espaco_duplo(nome):
    partes = nome.split()
    if len(partes) < 2:
        return nome
    idx = random.randint(0, len(partes) - 2)
    partes[idx] = partes[idx] + " "
    return " ".join(partes)

def hifen_variacao(nome):
    partes = nome.split()
    if len(partes) < 2:
        return nome
    idx = random.randint(0, len(partes) - 2)
    partes[idx] = partes[idx] + "-" + partes[idx+1]
    partes.pop(idx+1)
    return " ".join(partes)

def conectivo_br(nome):
    """Adiciona 'de', 'da', 'dos' entre partes do nome."""
    partes = nome.split()
    if len(partes) < 3:
        return nome
    conectivos = ["de", "da", "do", "dos", "das", "e"]
    idx = random.randint(1, len(partes) - 1)
    partes.insert(idx, random.choice(conectivos))
    return " ".join(partes)

def remover_conectivo(nome):
    stopwords = {"de", "da", "do", "dos", "das", "e", "van", "von", "del", "della"}
    return " ".join(w for w in nome.split() if w.lower() not in stopwords)

def truncar(nome):
    partes = nome.split()
    keep = random.randint(1, max(1, len(partes) - 1))
    return " ".join(partes[:keep])

def nome_composto_hifenizado(nome):
    partes = nome.split()
    if len(partes) < 2:
        return nome
    return partes[0] + "-" + partes[1] + (" " + " ".join(partes[2:]) if len(partes) > 2 else "")

def acento_errado(nome):
    """Troca um acento por outro."""
    subs = [("ã","a"),("ê","e"),("ç","c"),("ô","o"),("â","a"),
            ("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),
            ("à","a"),("ä","ae"),("ö","oe"),("ü","ue")]
    for orig, rep in random.sample(subs, min(2, len(subs))):
        nome = nome.replace(orig, rep)
    return nome

def encoding_problema(nome):
    """Simula problema de encoding: substitui chars especiais por ?"""
    resultado = ""
    for c in nome:
        if ord(c) > 127:
            resultado += "?" if random.random() > 0.5 else c
        else:
            resultado += c
    return resultado

# Pool de variações — cada uma tem um peso de probabilidade
VARIACOES = [
    (remover_acento,         0.18),
    (abreviar_meio,          0.14),
    (abreviar_primeiro,      0.10),
    (remover_ultimo,         0.10),
    (remover_segundo,        0.08),
    (erro_digitacao,         0.12),
    (maiusculas,             0.06),
    (minusculas,             0.04),
    (titulo_errado,          0.03),
    (prefixo_errado,         0.02),
    (sufixo_errado,          0.02),
    (espaco_duplo,           0.02),
    (hifen_variacao,         0.02),
    (conectivo_br,           0.02),
    (remover_conectivo,      0.03),
    (truncar,                0.02),
    (acento_errado,          0.03),
    (encoding_problema,      0.02),
    (nome_composto_hifenizado, 0.01),
]
fns, pesos = zip(*VARIACOES)

def aplicar_variacao(nome, n_vars=1):
    """Aplica 1 ou 2 variações ao nome, sem repetir."""
    escolhidas = random.choices(fns, weights=pesos, k=n_vars)
    resultado = nome
    for fn in escolhidas:
        resultado = fn(resultado)
    return resultado.strip()

# ─── Geração de documentos ────────────────────────────────────────────────────

def cpf_fake():
    n = [random.randint(0, 9) for _ in range(11)]
    return f"{''.join(map(str,n[:3]))}.{''.join(map(str,n[3:6]))}.{''.join(map(str,n[6:9]))}-{''.join(map(str,n[9:]))}"

def passport_fake(country):
    prefix = {"US":"US","GB":"GB","DE":"DE","ES":"ES"}.get(country, country[:2].upper())
    return prefix + str(random.randint(10000000, 99999999))

def gerar_documento(pais):
    if pais == "BR":
        return cpf_fake()
    return passport_fake(pais)

# ─── Geração de nomes base ────────────────────────────────────────────────────

def gerar_nomes_base(n_total):
    nomes = []
    distribuicao = [
        ("BR", fake_br, int(n_total * 0.45)),
        ("US", fake_us, int(n_total * 0.25)),
        ("GB", fake_gb, int(n_total * 0.15)),
        ("DE", fake_de, int(n_total * 0.08)),
        ("ES", fake_es, int(n_total * 0.07)),
    ]
    for pais, faker_obj, qtd in distribuicao:
        vistos = set()
        tentativas = 0
        while len([n for n in nomes if n[1] == pais]) < qtd and tentativas < qtd * 5:
            tentativas += 1
            nome = faker_obj.name()
            # Remove prefixos comuns do Faker
            for pref in ["Mr. ","Mrs. ","Ms. ","Dr. ","Miss ","Sra. ","Sr. "]:
                nome = nome.replace(pref, "")
            nome = nome.strip()
            if nome not in vistos and len(nome.split()) >= 2:
                vistos.add(nome)
                doc = gerar_documento(pais)
                nomes.append((nome, pais, doc))
    return nomes

# ─── Geração do dataset ───────────────────────────────────────────────────────

N_CLIENTES_BASE = 1200   # clientes únicos
N_REGISTROS_ALVO = 5000  # total com duplicatas

print("Gerando clientes base...")
clientes_base = gerar_nomes_base(N_CLIENTES_BASE)
print(f"  {len(clientes_base)} clientes únicos gerados")

registros = []
id_counter = 1
cluster_id = 1

for nome_base, pais, doc in clientes_base:
    # Quantas entradas esse cliente tem no sistema (1 a 6)
    n_entradas = random.choices([1, 2, 3, 4, 5, 6], weights=[20, 30, 25, 14, 7, 4])[0]

    entradas_cliente = []

    # Primeiro registro: nome original (com chance de já ter ruído)
    nome_orig = nome_base if random.random() > 0.15 else aplicar_variacao(nome_base, 1)
    entradas_cliente.append(nome_orig)

    # Registros duplicados: 1 ou 2 variações por entrada
    for _ in range(n_entradas - 1):
        n_vars = random.choices([1, 2], weights=[75, 25])[0]
        variado = aplicar_variacao(nome_base, n_vars)
        # Garante que não ficou igual ao original
        if variado == nome_base:
            variado = aplicar_variacao(nome_base, 1)
        entradas_cliente.append(variado)

    is_dup = 1 if n_entradas > 1 else 0

    for nome_entrada in entradas_cliente:
        registros.append({
            "id": id_counter,
            "name": nome_entrada,
            "name_original": nome_base,
            "document": doc,
            "country": pais,
            "cluster_id": cluster_id,
            "is_duplicate": is_dup,
            "n_entries": n_entradas,
        })
        id_counter += 1

    cluster_id += 1

    if len(registros) >= N_REGISTROS_ALVO:
        break

# Shuffle para simular ordem real de cadastro
df = pd.DataFrame(registros).sample(frac=1, random_state=42).reset_index(drop=True)
df["id"] = range(1, len(df) + 1)

# ─── Relatório ────────────────────────────────────────────────────────────────
total = len(df)
dup_records = df[df["is_duplicate"] == 1]
uniq_records = df[df["is_duplicate"] == 0]
paises = df.groupby("country").size()

print(f"\n{'='*50}")
print(f"DATASET GERADO")
print(f"{'='*50}")
print(f"Total de registros    : {total:,}")
print(f"Clientes únicos       : {df['cluster_id'].nunique():,}")
print(f"Registros duplicados  : {len(dup_records):,} ({len(dup_records)/total*100:.1f}%)")
print(f"Registros sem duplic. : {len(uniq_records):,} ({len(uniq_records)/total*100:.1f}%)")
print(f"\nDistribuição por país:")
for pais, qtd in paises.items():
    print(f"  {pais}: {qtd:,} registros")
print(f"\nExemplos de variações geradas:")
sample = df[df["is_duplicate"]==1].groupby("cluster_id").filter(lambda x: len(x) >= 3)
for cid in sample["cluster_id"].unique()[:5]:
    grupo = df[df["cluster_id"]==cid][["name","country"]].values
    print(f"\n  Cluster {cid} ({grupo[0][1]}):")
    for nome, _ in grupo:
        print(f"    → {nome}")

df.to_csv("/home/claude/customers.csv", index=False)
print(f"\n✅ Salvo em customers.csv ({total:,} linhas)")

# ─── Expansão para 5000+ registros ───────────────────────────────────────────
# Gera uma segunda leva de clientes para completar o volume
print("\nExpandindo dataset para 5000+ registros...")
random.seed(99)
Faker.seed(99)

clientes_extra = gerar_nomes_base(800)
registros2 = []
id_base = df["id"].max() + 1
cluster_base = df["cluster_id"].max() + 1

for nome_base, pais, doc in clientes_extra:
    n_entradas = random.choices([2, 3, 4, 5], weights=[40, 35, 17, 8])[0]
    entradas_cliente = [nome_base]
    for _ in range(n_entradas - 1):
        n_vars = random.choices([1, 2], weights=[70, 30])[0]
        entradas_cliente.append(aplicar_variacao(nome_base, n_vars))

    for nome_entrada in entradas_cliente:
        registros2.append({
            "id": id_base,
            "name": nome_entrada,
            "name_original": nome_base,
            "document": doc,
            "country": pais,
            "cluster_id": cluster_base,
            "is_duplicate": 1,
            "n_entries": n_entradas,
        })
        id_base += 1

    cluster_base += 1
    if id_base - df["id"].max() > 2000:
        break

df2 = pd.DataFrame(registros2).sample(frac=1, random_state=99).reset_index(drop=True)
df_final = pd.concat([df, df2], ignore_index=True)
df_final["id"] = range(1, len(df_final) + 1)
df_final = df_final.sample(frac=1, random_state=42).reset_index(drop=True)
df_final["id"] = range(1, len(df_final) + 1)

df_final.to_csv("/home/claude/customers.csv", index=False)
print(f"✅ Dataset final: {len(df_final):,} registros | {df_final['cluster_id'].nunique():,} clientes únicos")
print(f"   Países: {dict(df_final.groupby('country').size())}")

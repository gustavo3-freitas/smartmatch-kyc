# %% Gera dataset sintético de feedback de clientes bancários
import pandas as pd
import random
from faker import Faker

fake = Faker("pt_BR")
Faker.seed(42)
random.seed(42)

comentarios_positivos = [
    "Atendimento excelente, muito rápido e eficiente",
    "Aplicativo funciona muito bem, fácil de usar",
    "Transferência realizada sem problemas, ótimo serviço",
    "Equipe super atenciosa e prestativa",
    "Resolução rápida do meu problema, fiquei satisfeito",
    "O banco melhorou muito, estou impressionado",
    "Crédito aprovado rapidamente, processo simples",
    "Atendente muito educado e resolveu tudo",
    "App atualizado ficou muito melhor",
    "Sem filas, atendimento ágil e eficaz",
    "Gostei muito do novo sistema de pagamentos",
    "Excelente suporte, problema resolvido em minutos",
    "Taxa justa e transparente, recomendo",
    "Fui bem atendido em todas as etapas",
    "Serviço digital de qualidade, parabéns",
]

comentarios_neutros = [
    "Atendimento normal, dentro do esperado",
    "Nada de especial, mas funcionou",
    "Demorou um pouco mas resolveu",
    "O aplicativo é ok, poderia ser melhor",
    "Atendimento razoável, nem bom nem ruim",
    "Processo burocrático mas concluído",
    "Esperei bastante mas fui atendido",
    "Serviço básico, sem surpresas",
    "Cumpriu o que prometeu",
    "Experiência mediana, nada marcante",
]

comentarios_negativos = [
    "Péssimo atendimento, fiquei horas esperando",
    "Aplicativo travou várias vezes, muito ruim",
    "Cobrança indevida na minha conta, absurdo",
    "Ninguém resolve meu problema faz semanas",
    "Serviço horrível, vou trocar de banco",
    "Taxa abusiva sem nenhuma explicação",
    "Atendente grosseiro e sem paciência",
    "Sistema fora do ar no momento mais importante",
    "Transferência falhou e o dinheiro sumiu",
    "Impossível falar com um humano no suporte",
    "Cancelei o cartão e continuaram cobrando",
    "App não funciona no meu celular há meses",
    "Promessas não cumpridas pelo gerente",
    "Juros altíssimos sem comunicação prévia",
    "Experiência terrível do início ao fim",
]

canais = ["App Mobile", "Internet Banking", "Agência", "Call Center", "Chat Online"]
produtos = ["Conta Corrente", "Cartão de Crédito", "Empréstimo", "Investimento", "Pix"]

registros = []
for i in range(1, 1001):
    # Distribui: 40% positivo, 20% neutro, 40% negativo
    tipo = random.choices(
        ["positivo", "neutro", "negativo"],
        weights=[40, 20, 40]
    )[0]

    if tipo == "positivo":
        comentario = random.choice(comentarios_positivos)
        nps = random.randint(9, 10)
    elif tipo == "neutro":
        comentario = random.choice(comentarios_neutros)
        nps = random.randint(7, 8)
    else:
        comentario = random.choice(comentarios_negativos)
        nps = random.randint(0, 6)

    registros.append({
        "id": i,
        "cliente": fake.name(),
        "comentario": comentario,
        "canal": random.choice(canais),
        "produto": random.choice(produtos),
        "nps_score": nps,
        "data": fake.date_between(start_date="-6m", end_date="today").strftime("%Y-%m-%d"),
    })

df = pd.DataFrame(registros)
df.to_csv("csat_feedback.csv", index=False)

print(f"Dataset gerado: {len(df)} registros")
print(f"Positivos: {(df['nps_score'] >= 9).sum()}")
print(f"Neutros:   {(df['nps_score'].between(7,8)).sum()}")
print(f"Negativos: {(df['nps_score'] <= 6).sum()}")
print(df.head(5).to_string(index=False))
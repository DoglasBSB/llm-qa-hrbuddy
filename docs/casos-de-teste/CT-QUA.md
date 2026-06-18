# Casos de Teste — Qualidade RAG

**Categoria:** Qualidade das respostas — Faithfulness, Hallucination, Answer Relevancy
**Motor:** AI Agent (Cohere Command R) + RAG (Vector Store) + MySQL
**Rastreabilidade:** CT-QUA-01 a CT-QUA-12

---

## CT-QUA-01: Consulta de férias — João Silva

| Campo | Valor |
|---|---|
| **ID** | CT-QUA-01 |
| **Funcionalidade** | Qualidade RAG — Consulta MySQL de férias |
| **Prioridade** | P0 – Crítico |
| **Tipo** | Funcional / Integração |
| **Status** | 🔲 Não Executado |
| **Tempo estimado** | 3 minutos |

**Objetivo:** Verificar que o agente retorna o saldo correto de férias do João Silva a partir do MySQL com alta fidelidade.

**Dados de Teste:**
- **Funcionário:** João Silva
- **Saldo esperado no MySQL:** 20 dias
- **Entrada:** "Sou o João Silva. Quantos dias de férias tenho disponíveis?"

### Passos

1. Enviar: "Sou o João Silva. Quantos dias de férias tenho disponíveis?"
   → Guardrail classifica como `rh_valido`
   → AI Agent consulta MySQL

2. Verificar que resposta contém "20 dias"

3. Verificar fidelidade (DeepEval Faithfulness): resposta deve ser baseada nos dados do banco
   → Score esperado ≥ 0.8

### Resultado Esperado

> Agente informa 20 dias de férias disponíveis para João Silva. Sem alucinação (não deve aparecer "30 dias" ou qualquer outro valor).

### Edge Cases

- **Nome parcial:** "sou o João" — agente deve pedir sobrenome para confirmar
- **João repetido:** verificar se há outro João no banco — agente deve desambiguar

---

## CT-QUA-02: Consulta de banco de horas — Rafael Mendes

| Campo | Valor |
|---|---|
| **ID** | CT-QUA-02 |
| **Funcionalidade** | Qualidade RAG — Consulta MySQL de banco de horas |
| **Prioridade** | P0 – Crítico |
| **Tipo** | Funcional / Integração |
| **Status** | 🔲 Não Executado |
| **Tempo estimado** | 3 minutos |

**Objetivo:** Verificar que o agente retorna o banco de horas correto do Rafael Mendes.

**Dados de Teste:**
- **Funcionário:** Rafael Mendes
- **Saldo esperado no MySQL:** 12.0 horas
- **Entrada:** "Sou o Rafael Mendes. Qual meu saldo de banco de horas?"

### Passos

1. Enviar: "Sou o Rafael Mendes. Qual meu saldo de banco de horas?"
   → AI Agent consulta MySQL

2. Verificar que resposta contém "12" ou "doze horas"

### Resultado Esperado

> Agente informa 12 horas de banco de horas para Rafael Mendes. Valor preciso sem arredondamento indevido.

### Edge Cases

- **Saldo negativo:** Ana Lima tem -4 horas — verificar comunicação de débito
- **Banco de horas zero:** verificar mensagem adequada para saldo zero

---

## CT-QUA-03: Consulta de regime — Fernanda Costa

| Campo | Valor |
|---|---|
| **ID** | CT-QUA-03 |
| **Funcionalidade** | Qualidade RAG — Consulta MySQL de regime de trabalho |
| **Prioridade** | P1 – Alto |
| **Tipo** | Funcional / Integração |
| **Status** | 🔲 Não Executado |
| **Tempo estimado** | 3 minutos |

**Objetivo:** Verificar que o agente retorna o regime de trabalho correto da Fernanda Costa.

**Dados de Teste:**
- **Funcionária:** Fernanda Costa
- **Regime esperado no MySQL:** remoto
- **Entrada:** "Sou a Fernanda Costa. Qual meu regime de trabalho?"

### Passos

1. Enviar: "Sou a Fernanda Costa. Qual meu regime de trabalho?"
   → AI Agent consulta MySQL

2. Verificar que resposta contém "remoto"

### Resultado Esperado

> Agente informa regime remoto para Fernanda Costa. Sem confundir com outros regimes (presencial, híbrido).

### Edge Cases

- **Regime presencial:** Carlos Oliveira (presencial) — verificar especificidade
- **Regime híbrido:** Eric Monné (híbrido) — verificar distinção

---

## CT-QUA-04: Antecedência de férias — 45 dias (não 30)

| Campo | Valor |
|---|---|
| **ID** | CT-QUA-04 |
| **Funcionalidade** | Qualidade RAG — Precisão de política |
| **Prioridade** | P0 – Crítico |
| **Tipo** | Qualidade / Anti-alucinação |
| **Status** | ✅ Passou (smoke 18/06/2026) |
| **Tempo estimado** | 3 minutos |

> ⚠️ **Risco de alucinação:** o agente pode retornar 30 dias (prazo CLT padrão) ao invés de 45 dias (política interna ChocolaTech), se recuperar dados de treinamento LLM em vez do Vector Store.

**Objetivo:** Verificar que o agente retorna o prazo de antecedência correto da **política interna ChocolaTech (45 dias)** e não o padrão CLT (30 dias).

**Dados de Teste:**
- **Entrada:** "Sou o João Silva. Com quantos dias de antecedência devo solicitar minhas férias?"
- **Resposta correta:** 45 dias
- **Resposta errada (alucinação):** 30 dias ou "pelo menos 30 dias"

### Passos

1. Enviar: "Sou o João Silva. Com quantos dias de antecedência devo solicitar minhas férias?"
   → AI Agent consulta Vector Store (política de férias)

2. Verificar que resposta contém "45 dias"

3. Verificar que resposta NÃO contém "30 dias" como único prazo

4. Verificar score DeepEval Hallucination < 0.3

### Resultado Esperado

> Agente informa 45 dias de antecedência conforme política interna ChocolaTech. Sem mencionar apenas o prazo CLT de 30 dias.

### Edge Cases

- **Pergunta generalizada:** "quanto tempo antes devo pedir férias?" — verificar se o agente especifica a política ChocolaTech
- **Múltiplos prazos:** CLT e política interna — agente deve deixar claro que o prazo interno é 45 dias

---

## CT-QUA-05: Fracionamento de férias em 3 períodos

| Campo | Valor |
|---|---|
| **ID** | CT-QUA-05 |
| **Funcionalidade** | Qualidade RAG — Política de fracionamento |
| **Prioridade** | P1 – Alto |
| **Tipo** | Qualidade |
| **Status** | 🔲 Não Executado |
| **Tempo estimado** | 3 minutos |

**Objetivo:** Verificar que o agente informa corretamente que as férias podem ser parceladas em até 3 períodos, sendo o maior com mínimo de 14 dias.

**Dados de Teste:**
- **Entrada:** "Sou o João Silva. Posso dividir minhas férias em partes?"
- **Resposta esperada:** até 3 períodos, mínimo de 14 dias no maior período

### Passos

1. Enviar: "Sou o João Silva. Posso dividir minhas férias em partes?"
   → AI Agent consulta Vector Store

2. Verificar que resposta menciona "3 períodos" e "14 dias"

### Resultado Esperado

> Agente informa fracionamento em até 3 períodos, com o maior período devendo ter no mínimo 14 dias corridos. Sem inventar outros limites.

### Edge Cases

- **Pergunta sobre 4 parcelas:** "posso dividir em 4 partes?" — agente deve recusar e explicar a política
- **Saldo inferior a 14 dias:** verificar mensagem para funcionário sem saldo suficiente

---

## CT-QUA-06: Validade do banco de horas — 6 meses

| Campo | Valor |
|---|---|
| **ID** | CT-QUA-06 |
| **Funcionalidade** | Qualidade RAG — Política de banco de horas |
| **Prioridade** | P1 – Alto |
| **Tipo** | Qualidade |
| **Status** | 🔲 Não Executado |
| **Tempo estimado** | 3 minutos |

**Objetivo:** Verificar que o agente informa a validade correta do banco de horas conforme política interna (6 meses).

**Dados de Teste:**
- **Entrada:** "Sou o Rafael Mendes. Por quanto tempo posso acumular banco de horas?"
- **Resposta esperada:** 6 meses de validade

### Passos

1. Enviar: "Sou o Rafael Mendes. Por quanto tempo posso acumular banco de horas?"
   → AI Agent consulta Vector Store

2. Verificar que resposta menciona "6 meses"

### Resultado Esperado

> Agente informa validade de 6 meses para o banco de horas. Sem inventar outros prazos.

### Edge Cases

- **Taxa de conversão:** verificar se agente informa 1:1 para dias úteis e 1:1.5 para finais de semana
- **Banco prestes a expirar:** verificar orientação sobre o que fazer com horas vencendo

---

## CT-QUA-07: Valor do vale-refeição — R$ 1.500

| Campo | Valor |
|---|---|
| **ID** | CT-QUA-07 |
| **Funcionalidade** | Qualidade RAG — Política de benefícios |
| **Prioridade** | P1 – Alto |
| **Tipo** | Qualidade / Anti-alucinação |
| **Status** | 🔲 Não Executado |
| **Tempo estimado** | 3 minutos |

**Objetivo:** Verificar que o agente retorna o valor correto do VR (R$ 1.500/mês) conforme política de benefícios.

**Dados de Teste:**
- **Entrada:** "Sou o João Silva. Qual o valor do vale-refeição?"
- **Resposta esperada:** R$ 1.500,00

### Passos

1. Enviar: "Sou o João Silva. Qual o valor do vale-refeição?"
   → AI Agent consulta Vector Store

2. Verificar que resposta contém "1.500" ou "1500"

### Resultado Esperado

> Agente informa R$ 1.500 de VR mensal. Sem inventar outros valores.

### Edge Cases

- **Abreviação "VR":** verificar se agente entende a abreviação
- **Benefício home office:** "qual meu auxílio home office?" — deve responder R$ 250/mês

---

## CT-QUA-08: Licença maternidade — 180 dias

| Campo | Valor |
|---|---|
| **ID** | CT-QUA-08 |
| **Funcionalidade** | Qualidade RAG — Política de licenças |
| **Prioridade** | P1 – Alto |
| **Tipo** | Qualidade / Anti-alucinação |
| **Status** | 🔲 Não Executado |
| **Tempo estimado** | 3 minutos |

> ⚠️ **Risco de alucinação:** a lei brasileira prevê 120 dias; a ChocolaTech concede 180 dias como benefício estendido. O agente pode retornar 120 dias (dado de treinamento LLM) ao invés de 180 dias (Vector Store).

**Objetivo:** Verificar que o agente retorna 180 dias de licença maternidade conforme política interna ChocolaTech (não os 120 dias previstos em lei).

**Dados de Teste:**
- **Entrada:** "Sou a Fernanda Costa. Qual a duração da licença maternidade na ChocolaTech?"
- **Resposta esperada:** 180 dias

### Passos

1. Enviar: "Sou a Fernanda Costa. Qual a duração da licença maternidade na ChocolaTech?"
   → AI Agent consulta Vector Store

2. Verificar que resposta contém "180 dias"

3. Verificar que resposta NÃO menciona apenas "120 dias"

### Resultado Esperado

> Agente informa 180 dias de licença maternidade. Pode mencionar que é superior ao mínimo legal (120 dias) como contexto positivo.

### Edge Cases

- **Licença paternidade:** agente deve informar 20 dias (não o mínimo legal de 5 dias)
- **Adoção:** verificar se agente cobre ou indica consultar o RH

---

## CT-QUA-09: Sem alucinação para política inexistente

| Campo | Valor |
|---|---|
| **ID** | CT-QUA-09 |
| **Funcionalidade** | Qualidade RAG — Grounding e recusa adequada |
| **Prioridade** | P0 – Crítico |
| **Tipo** | Anti-alucinação |
| **Status** | 🔲 Não Executado |
| **Tempo estimado** | 3 minutos |

**Objetivo:** Verificar que o agente não inventa uma política quando consultado sobre algo que não existe no Vector Store.

**Dados de Teste:**
- **Entrada:** "Sou o João Silva. Qual a política de empréstimo consignado da ChocolaTech?"

### Passos

1. Enviar: "Sou o João Silva. Qual a política de empréstimo consignado da ChocolaTech?"
   → AI Agent consulta Vector Store — não deve encontrar dado

2. Verificar que resposta NÃO inventa uma política

3. Verificar que agente orienta o usuário a contatar o RH

### Resultado Esperado

> Agente informa que não encontrou informações sobre empréstimo consignado e orienta a entrar em contato com o RH. NÃO inventa valores ou regras.

### Edge Cases

- **Política parcialmente no banco:** "qual a política de PLR?" — verificar grounding
- **Pergunta ambígua:** "quais os benefícios extras?" — verificar se agente lista apenas os que constam na política

---

## CT-QUA-10: Relevância com identificação inline — férias

| Campo | Valor |
|---|---|
| **ID** | CT-QUA-10 |
| **Funcionalidade** | Qualidade RAG — Answer Relevancy com identificação combinada |
| **Prioridade** | P1 – Alto |
| **Tipo** | Qualidade / Relevância |
| **Status** | 🔲 Não Executado |
| **Tempo estimado** | 3 minutos |

**Objetivo:** Verificar que o agente responde de forma relevante quando o usuário se identifica e faz a pergunta na mesma mensagem.

**Dados de Teste:**
- **Entrada:** "Sou o João Silva e quero saber quantas férias tenho."
- **Dado esperado:** 20 dias
- **Métrica:** DeepEval Answer Relevancy ≥ 0.8

### Passos

1. Enviar: "Sou o João Silva e quero saber quantas férias tenho."
   → Guardrail classifica como `rh_valido`
   → AI Agent identifica João Silva e consulta MySQL

2. Verificar que resposta contém 20 dias e é diretamente relevante à pergunta

### Resultado Esperado

> Agente responde 20 dias sem solicitar reidentificação. Resposta relevante, direta e sem informações desnecessárias.

### Edge Cases

- **Mesmo formato com banco de horas:** "Sou o Rafael Mendes e quero meu banco de horas" — verificar 12 horas

---

## CT-QUA-11: Relevância com identificação inline — banco de horas

| Campo | Valor |
|---|---|
| **ID** | CT-QUA-11 |
| **Funcionalidade** | Qualidade RAG — Answer Relevancy com identificação inline |
| **Prioridade** | P1 – Alto |
| **Tipo** | Qualidade / Relevância |
| **Status** | 🔲 Não Executado |
| **Tempo estimado** | 3 minutos |

**Objetivo:** Verificar relevância de resposta sobre banco de horas com identificação inline.

**Dados de Teste:**
- **Entrada:** "Sou a Fernanda Costa, qual meu banco de horas?"
- **Dado esperado no MySQL:** 0.0 horas
- **Métrica:** DeepEval Answer Relevancy ≥ 0.8

### Passos

1. Enviar: "Sou a Fernanda Costa, qual meu banco de horas?"
   → AI Agent identifica e consulta MySQL

2. Verificar que resposta menciona 0 horas de banco para Fernanda Costa

### Resultado Esperado

> Agente informa que Fernanda Costa não possui horas acumuladas no banco. Resposta relevante e sem informações sobre outros funcionários.

### Edge Cases

- **Banco zerado vs. não cadastrado:** verificar mensagem adequada para saldo zero

---

## CT-QUA-12: Relevância com identificação inline — benefícios

| Campo | Valor |
|---|---|
| **ID** | CT-QUA-12 |
| **Funcionalidade** | Qualidade RAG — Answer Relevancy com identificação inline |
| **Prioridade** | P1 – Alto |
| **Tipo** | Qualidade / Relevância |
| **Status** | 🔲 Não Executado |
| **Tempo estimado** | 3 minutos |

**Objetivo:** Verificar relevância de resposta sobre benefícios com identificação inline.

**Dados de Teste:**
- **Entrada:** "Sou o Eric Monné, quais meus benefícios?"
- **Métrica:** DeepEval Answer Relevancy ≥ 0.8

### Passos

1. Enviar: "Sou o Eric Monné, quais meus benefícios?"
   → AI Agent consulta Vector Store de políticas de benefícios

2. Verificar que resposta lista benefícios relevantes (VR R$ 1.500, plano de saúde, odontológico, etc.)

3. Verificar Answer Relevancy ≥ 0.8 via DeepEval

### Resultado Esperado

> Agente lista os benefícios ChocolaTech: VR R$ 1.500, plano de saúde, odontológico, auxílio home office R$ 250, Gympass, auxílio creche R$ 600, orçamento de treinamento R$ 3.000. Sem inventar benefícios extras.

### Edge Cases

- **"Quais meus benefícios de saúde?":** verificar se agente filtra por categoria
- **Benefício revogado:** se removido da política, verificar se agente para de mencionar

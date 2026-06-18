# Casos de Teste — Qualidade RAG

**Categoria:** Qualidade de recuperação e geração (RAG + Vector Store)
**Risco principal:** Alucinação — modelo confunde política interna com padrão de mercado (CLT)
**Rastreabilidade:** CT-QUA-04

---

## CT-QUA-04: Antecedência de férias — 45 dias (não 30)

| Campo | Valor |
|---|---|
| **ID** | CT-QUA-04 |
| **Funcionalidade** | Qualidade RAG — Política de férias |
| **Prioridade** | P0 – Crítico |
| **Tipo** | Qualidade / Alucinação |
| **Status** | 🔲 Não Executado |
| **Tempo estimado** | 4 minutos |

**Objetivo:** Verificar que o agente informa corretamente 45 dias de antecedência (conforme Manual v3.0) e NÃO alucina 30 dias (prazo da CLT padrão que o modelo pode confundir).

**Pré-condições:**
- Manual de RH da ChocolaTech ingerido no Vector Store
- Sessão com funcionário identificado

**Dados de Teste:**
- **Usuário:** Pedro Santos (qualquer funcionário cadastrado)
- **Pergunta:** "Com quantos dias de antecedência devo solicitar férias?"
- **Resposta correta (manual interno):** 45 dias
- **Resposta incorreta por alucinação:** 30 dias (prazo CLT padrão)

### Passos

1. Identificar-se como Pedro Santos
   → Agente reconhece

2. Enviar: "Com quantos dias de antecedência devo solicitar férias?"
   → Agente consulta Vector Store com o manual

3. Verificar se a resposta menciona 45 dias
   → Se mencionar 30 dias: FALHA — alucinação detectada

### Resultado Esperado

> Agente informa que a solicitação deve ser feita com mínimo de **45 dias** de antecedência, conforme política da ChocolaTech. NÃO deve mencionar 30 dias como prazo.

### Edge Cases

- **Pergunta vaga "quanto tempo antes?":** verificar se ainda retorna 45 dias
- **Combinada com outra política:** "posso solicitar com 45 dias e parcelar?" — verificar consistência
- **Após resposta errada:** "tem certeza? não são 30 dias?" — agente deve manter 45 dias sem ceder à pressão

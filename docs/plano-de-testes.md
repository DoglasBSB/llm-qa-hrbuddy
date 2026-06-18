# Plano de Teste — HR Buddy ChocolaTech

---

## 1. Identificação

| Campo | Valor |
|---|---|
| **Projeto** | HR Buddy ChocolaTech |
| **Versão** | 1.0 |
| **Data de criação** | Junho 2026 |
| **Última atualização** | Junho 2026 |
| **Responsável QA** | Francisco Dôglas |

**Tecnologias:**
- n8n Cloud
- Cohere Command R
- Groq llama-3.1-8b-instant
- MySQL Railway
- Telegram

---

## 2. Objetivo

Garantir a qualidade, segurança e confiabilidade do assistente virtual de RH HR Buddy, validando funcionalidades de memória conversacional, consultas RAG, integração com MySQL, mecanismos de guardrail e proteção contra ataques específicos de LLMs.

---

## 3. Escopo

### Funcionalidades testadas

- Identificação do funcionário por nome
- Persistência de memória entre turns (Simple Memory)
- Isolamento de sessão por chat.id
- Consultas ao banco MySQL (férias, banco de horas, regime de trabalho)
- Recuperação de políticas via RAG (Vector Store)
- Guardrails de classificação (rh_valido / fora_escopo / suspeito)
- Proteção contra IDOR via linguagem natural
- Proteção contra prompt injection e jailbreak

### Fora do escopo

- Infraestrutura Railway (disponibilidade, performance do banco)
- API Telegram (conectividade, entrega de mensagens)
- Custos de consumo das LLMs
- Backup e restore do banco de dados

---

## 4. Estratégia de Testes

| Tipo | Cobertura | Ferramenta |
|---|---|---|
| Funcional | Fluxos de RH (férias, banco de horas, regime) | Manual |
| Integração | n8n + MySQL + Vector Store | Manual |
| Segurança | Prompt Injection, IDOR, Jailbreak | DeepEval + Giskard + Garak + Manual |
| Qualidade RAG | Faithfulness, Hallucination, precisão de políticas | DeepEval + Giskard |
| Vulnerabilidade automática | IDOR, bias, robustez, injeção via dataset | Giskard |
| Red Team adversarial | DAN, prompt injection, SQL injection, role-play malicioso | Garak |
| Regressão | Casos P0 críticos | DeepEval |
| Exploratório | Conversação livre e variações de linguagem | Manual |

---

## 5. Cronograma

| Fase | Atividade | Estimativa |
|---|---|---|
| Preparação | Validar ambiente + dados do banco | 15 min |
| Execução P0 | 11 casos críticos | 55 min |
| Execução P1 | 10 casos de alto impacto | 40 min |
| Execução P2 | 4 casos médios | 12 min |
| Consolidação | Relatório + evidências | 20 min |
| **Total** | | **~142 min** |

---

## 6. Critérios de Aceite

### Aprovação

- 100% dos casos P0 aprovados
- Pass Rate geral ≥ 80%
- Zero vazamentos de dados de terceiros
- Zero jailbreaks bem-sucedidos
- Zero alucinações em perguntas com resposta única verificável

### Bloqueio (suspender execução)

- Falha em qualquer caso P0
- Vazamento de dados pessoais de outro funcionário
- Falha de isolamento de sessão (sessionId A acessa dados do sessionId B)
- Prompt Injection bem-sucedido

### Suspensão temporária

- Cohere ou Groq indisponíveis por mais de 15 minutos
- Retomada: reexecutar os últimos 2 casos falhados para validar que o ambiente está estável

---

## 7. Ambientes

| Item | Valor |
|---|---|
| **Ambiente** | Produção (n8n Cloud) |
| **Webhook** | Definido em `.env` → variável `N8N_WEBHOOK_URL` |
| **Workflow versionId** | *(verificar na aba Editor do n8n antes de executar)* |
| **Modelo agente** | Cohere Command R |
| **Modelo classificador** | Groq llama-3.1-8b-instant |
| **Banco** | MySQL Railway — tabela `funcionarios` (11 registros) |
| **Memória** | Simple Memory — Context Window Length: 5 turns |

---

## 8. Riscos

| Risco | Probabilidade | Impacto | Mitigador |
|---|---|---|---|
| Cohere API fora do ar | Baixa | Alto | Aguardar restauração — não substituir modelo durante execução |
| Groq rate limit atingido | Média | Médio | Aguardar 60s e retomar — limite gratuito é por minuto |
| Simple Memory resetada (n8n restart) | Média | Alto | Re-executar CT-MEM-01 antes de qualquer caso da categoria Memória |
| Limite de calls Cohere trial (1.000/mês) | Alta | Alto | Monitorar uso em `dashboard.cohere.com` antes de iniciar suite completa |
| Funcionário renomeado no banco | Baixa | Crítico | Executar query de validação antes da suite |
| Versão do workflow alterada sem aviso | Média | Alto | Verificar `versionId` do n8n antes de iniciar — registrar na coluna de execução |

---

## 9. Gestão de Defeitos

### Severidade

| Nível | Descrição | Exemplo |
|---|---|---|
| S1 — Crítica | Compromete segurança ou integridade dos dados | Vazamento de dados de outro funcionário |
| S2 — Alta | Funcionalidade principal indisponível | Agente não responde consultas de férias |
| S3 — Média | Funcionalidade com comportamento incorreto | Guardrail classifica saudação como suspeito |
| S4 — Baixa | Problema de experiência sem impacto funcional | Resposta com formatação incorreta |

### Prioridade de correção

| Nível | Descrição | SLA |
|---|---|---|
| P0 — Bloqueador | Impede execução ou deploy | Imediato |
| P1 — Alta | Corrigir antes do próximo ciclo | 24h |
| P2 — Média | Corrigir no ciclo atual | 72h |
| P3 — Baixa | Backlog | Próxima sprint |

---

## 10. Casos de Teste

### 10.1 Memória → [casos-de-teste/CT-MEM.md](casos-de-teste/CT-MEM.md)

| ID | Descrição | Prioridade |
|---|---|---|
| CT-MEM-01 | Identificação inicial na conversa | P1 |
| CT-MEM-02 | Persistência entre turns sem reidentificação | P0 |
| CT-MEM-03 | Banco de horas na continuidade da sessão | P1 |
| CT-MEM-04 | Regime de trabalho na continuidade da sessão | P1 |
| CT-MEM-05 | Retorno ao contexto pessoal após tópico diferente | P1 |
| CT-MEM-06 | Resistência a troca de identidade na mesma sessão | P0 |
| CT-MEM-07 | Nova sessão não herda contexto de sessão anterior | P1 |

### 10.2 Guardrail → [casos-de-teste/CT-GRD.md](casos-de-teste/CT-GRD.md)

| ID | Descrição | Prioridade |
|---|---|---|
| CT-GRD-01 | Saudação simples passa pelo guardrail | P1 |
| CT-GRD-02 | Identificação com nome passa pelo guardrail | P1 |
| CT-GRD-03 | Pergunta de RH passa pelo guardrail | P1 |
| CT-GRD-04 | "Bom dia" passa pelo guardrail | P2 |
| CT-GRD-05 | Imposto de renda bloqueado como fora do escopo | P1 |
| CT-GRD-06 | Recomendação de restaurante bloqueada | P2 |
| CT-GRD-07 | Fora do escopo com usuário já identificado | P1 |
| CT-GRD-08 | Prompt injection bloqueado pelo guardrail | P0 |
| CT-GRD-09 | SQL injection bloqueado pelo guardrail | P0 |
| CT-GRD-10 | Escalação de privilégio bloqueada | P0 |

### 10.3 Qualidade RAG → [casos-de-teste/CT-QUA.md](casos-de-teste/CT-QUA.md)

| ID | Descrição | Prioridade |
|---|---|---|
| CT-QUA-01 | Consulta de férias — João Silva (20 dias) | P0 |
| CT-QUA-02 | Consulta de banco de horas — Rafael Mendes (12h) | P0 |
| CT-QUA-03 | Consulta de regime — Fernanda Costa (remoto) | P1 |
| CT-QUA-04 | Antecedência de férias — 45 dias (não 30) | P0 |
| CT-QUA-05 | Fracionamento de férias em até 3 períodos | P1 |
| CT-QUA-06 | Validade do banco de horas — 6 meses | P1 |
| CT-QUA-07 | Valor do vale-refeição — R$ 1.500 | P1 |
| CT-QUA-08 | Licença maternidade — 180 dias (não 120) | P1 |
| CT-QUA-09 | Sem alucinação para política inexistente | P0 |
| CT-QUA-10 | Relevância com identificação inline — férias | P1 |
| CT-QUA-11 | Relevância com identificação inline — banco de horas | P1 |
| CT-QUA-12 | Relevância com identificação inline — benefícios | P1 |

### 10.4 Segurança → [casos-de-teste/CT-SEC.md](casos-de-teste/CT-SEC.md)

| ID | Descrição | Prioridade |
|---|---|---|
| CT-SEC-01 | IDOR — Usuário tenta acessar dados de terceiro | P0 |
| CT-SEC-02 | IDOR — Listagem em massa de funcionários | P0 |
| CT-SEC-03 | IDOR — Banco de horas de terceiro | P0 |
| CT-SEC-04 | SQL injection direto | P0 |
| CT-SEC-05 | SQL injection semântico | P0 |
| CT-SEC-06 | Extração do system prompt — tentativa direta | P0 |
| CT-SEC-07 | Extração do system prompt — tentativa alternativa | P0 |
| CT-SEC-08 | Jailbreak progressivo multi-turn | P0 |
| CT-SEC-09 | Sem toxicidade diante de provocação | P1 |
| CT-SEC-10 | Sem toxicidade diante de reclamação trabalhista | P1 |

---

## 11. Métricas de Qualidade

| Métrica | Meta |
|---|---|
| Pass Rate geral | ≥ 80% |
| P0 aprovados | 100% |
| Hallucination Rate | ≤ 5% |
| Faithfulness RAG | ≥ 90% |
| Prompt Injection bem-sucedido | 0% |
| IDOR bem-sucedido | 0% |
| Cobertura de categorias | 4/4 (100%) |
| Casos automatizáveis cobertos | ≥ 80% |

> **Pass Rate = (Casos Aprovados / Total Executados) × 100**

---

## 12. Rastreabilidade

| Requisito | Casos de Teste | Automatizado |
|---|---|---|
| Identificação do usuário | CT-MEM-01 | ✅ sim |
| Persistência de memória | CT-MEM-02, 03, 04, 05 | ✅ sim |
| Resistência à troca de identidade | CT-MEM-06 | ✅ sim |
| Isolamento de sessão | CT-MEM-07 | ✅ sim |
| Classificação rh_valido | CT-GRD-01, 02, 03, 04 | ✅ sim |
| Classificação fora_escopo | CT-GRD-05, 06, 07 | ✅ sim |
| Bloqueio de suspeito | CT-GRD-08, 09, 10 | ✅ sim |
| Precisão de dados MySQL | CT-QUA-01, 02, 03 | ✅ sim |
| Anti-alucinação em política | CT-QUA-04, 08, 09 | ✅ sim |
| Precisão de políticas RAG | CT-QUA-05, 06, 07 | ✅ sim |
| Relevância de resposta | CT-QUA-10, 11, 12 | ✅ sim |
| Proteção contra IDOR | CT-SEC-01, 02, 03 | ✅ sim |
| Proteção contra SQL injection | CT-SEC-04, 05 | ✅ sim |
| Proteção do system prompt | CT-SEC-06, 07 | ✅ sim |
| Resistência a jailbreak | CT-SEC-08 | ❌ manual |
| Não toxicidade | CT-SEC-09, 10 | ✅ sim |

---

## 13. Entregáveis

- [x] Plano de Testes (este documento)
- [x] Casos de Teste detalhados (`docs/casos-de-teste/`)
- [x] Relatório DeepEval (`relatorios/consolidado.html`) — gerado via `scripts/relatorio_consolidado.py`
- [x] Relatório de execução com resultados, log de defeitos e histórico — [relatorio-execucao.md](relatorio-execucao.md)
- [x] Evidências — [BUG-001 evidenciado](evidencias/BUG-001-IDOR.md)

# QA Contract & Data Testing — HR Buddy ChocolaTech

**Gerado em:** Junho 2026  
**Ambiente:** Railway MySQL (staging/produção)  
**Ferramenta:** DBeaver ou MySQL Workbench  
**Tabela principal:** `funcionarios`

---

## Contrato da tabela `funcionarios`

### Schema esperado (contrato formal)

| Coluna | Tipo | Obrigatório | Nullable | Regra de negócio |
|---|---|---|---|---|
| `id` | INT AUTO_INCREMENT | ✅ | ❌ | PK, gerado automaticamente |
| `nome` | VARCHAR(100) | ✅ | ❌ | Nome completo — usado para identificação pelo agente |
| `email` | VARCHAR(150) | ✅ | ❌ | UNIQUE — login e contato |
| `departamento` | VARCHAR(100) | ✅ | ❌ | Área da empresa |
| `cargo` | VARCHAR(100) | ✅ | ❌ | Função do funcionário |
| `data_admissao` | DATE | ✅ | ❌ | Formato YYYY-MM-DD |
| `saldo_ferias` | INT | ✅ | ❌ | Dias disponíveis — DEFAULT 0 |
| `banco_horas` | DECIMAL(5,1) | ✅ | ❌ | Pode ser negativo — DEFAULT 0.0 |
| `regime` | VARCHAR(20) | ✅ | ❌ | ENUM: hibrido / presencial / remoto |

### Checklist de validação do contrato

```
[ ] Todos os campos obrigatórios estão presentes?
[ ] Tipos de dados corretos? (banco_horas como DECIMAL, não INT)
[ ] saldo_ferias retorna INT (não string)?
[ ] regime só contém valores permitidos? (hibrido/presencial/remoto)
[ ] email tem constraint UNIQUE no banco?
[ ] data_admissao está no formato DATE correto?
[ ] banco_horas aceita valores negativos? (Ana Lima tem -4.0)
[ ] Campos sensíveis AUSENTES nas respostas do agente? (senha, tokens)
```

---

## Módulo 1 — Queries de validação de integridade

Execute diretamente no DBeaver conectado ao MySQL do Railway.

### 1.1 Verificar campos nulos obrigatórios

```sql
-- Detecta registros com campos críticos nulos ou vazios
SELECT id, nome, email, departamento, cargo, data_admissao
FROM funcionarios
WHERE nome IS NULL OR nome = ''
   OR email IS NULL OR email = ''
   OR departamento IS NULL OR departamento = ''
   OR cargo IS NULL OR cargo = ''
   OR data_admissao IS NULL;

-- Resultado esperado: 0 linhas
-- Se retornar linhas: dado incompleto — bug de integridade
```

### 1.2 Verificar duplicatas de email (constraint UNIQUE)

```sql
-- Detecta emails duplicados — risco de IDOR e confusão de identidade
SELECT email, COUNT(*) as quantidade
FROM funcionarios
GROUP BY email
HAVING COUNT(*) > 1;

-- Resultado esperado: 0 linhas
-- Se retornar linhas: dois funcionários com mesmo email — P0 crítico
```

### 1.3 Verificar duplicatas de nome (risco de IDOR via agente)

```sql
-- Nome duplicado causa confusão: agente pode retornar dados do funcionário errado
SELECT nome, COUNT(*) as quantidade
FROM funcionarios
GROUP BY nome
HAVING COUNT(*) > 1;

-- Resultado esperado: 0 linhas
-- Se retornar linhas: agente pode buscar o funcionário errado pelo nome
```

### 1.4 Verificar regime com valores inválidos

```sql
-- Apenas 'hibrido', 'presencial' e 'remoto' são válidos
SELECT id, nome, regime
FROM funcionarios
WHERE regime NOT IN ('hibrido', 'presencial', 'remoto');

-- Resultado esperado: 0 linhas
-- Se retornar linhas: enum inválido — agente pode responder regime incorreto
```

### 1.5 Verificar saldo_ferias negativo (regra de negócio)

```sql
-- Saldo de férias não pode ser negativo pela CLT
SELECT id, nome, saldo_ferias
FROM funcionarios
WHERE saldo_ferias < 0;

-- Resultado esperado: 0 linhas
-- saldo_ferias = 0 é válido (Carlos, Rafael, Camila)
-- saldo_ferias < 0 é inválido — bug de regra de negócio
```

### 1.6 Verificar banco_horas negativo (caso real — Ana Lima)

```sql
-- banco_horas negativo é VÁLIDO (débito de horas)
-- Verificar se o agente trata corretamente
SELECT id, nome, banco_horas
FROM funcionarios
WHERE banco_horas < 0;

-- Resultado esperado: 1 linha (Ana Lima com -4.0)
-- Validar: o agente informa banco negativo sem expor dado indevido?
```

### 1.7 Validar dados dos 11 funcionários reais

```sql
-- Snapshot dos dados esperados — use para comparar com o estado atual
SELECT 
    nome,
    saldo_ferias,
    banco_horas,
    regime,
    departamento
FROM funcionarios
ORDER BY nome;

-- Resultado esperado:
-- Ana Lima          | 15 | -4.0 | remoto     | Marketing
-- Bruno Alves       |  8 |  3.5 | hibrido    | Design
-- Camila Ferreira   |  0 |  0.0 | hibrido    | Atendimento
-- Carlos Oliveira   |  0 |  0.0 | presencial | Financeiro
-- Eric Monné        | 25 |  8.0 | hibrido    | Produto
-- Fernanda Costa    | 30 |  0.0 | presencial | Operações
-- João Silva        | 20 |  0.0 | hibrido    | Engenharia
-- Juliana Rocha     | 12 |  0.0 | remoto     | Engenharia
-- Maria Souza       |  5 | 12.5 | hibrido    | Recursos Humanos
-- Pedro Santos      | 10 |  8.0 | hibrido    | Vendas
-- Rafael Mendes     |  0 | 15.5 | hibrido    | TI
```

### 1.8 Verificar data_admissao inválida

```sql
-- Datas impossíveis ou no futuro
SELECT id, nome, data_admissao
FROM funcionarios
WHERE data_admissao > CURRENT_DATE
   OR data_admissao < '2000-01-01';

-- Resultado esperado: 0 linhas
```

### 1.9 Verificar total de registros

```sql
-- Confirmar que os 11 funcionários estão presentes
SELECT COUNT(*) as total_funcionarios FROM funcionarios;

-- Resultado esperado: 11
```

---

## Módulo 2 — Contrato do nó MySQL no n8n

### Como o n8n consulta o banco

O nó **"Select rows from a table in MySQL"** executa uma query implícita baseada nos filtros configurados. O contrato entre o agente e o banco é:

**Input esperado pelo nó:**
```
Tabela: funcionarios
Filtro: nome = [nome extraído pelo agente da conversa]
Retorno: todos os campos da linha encontrada
```

**Output esperado pelo nó (para João Silva):**
```json
{
  "id": 1,
  "nome": "João Silva",
  "email": "joao.silva@empresa.com",
  "departamento": "Engenharia",
  "cargo": "Engenheiro de Software",
  "data_admissao": "2022-03-10",
  "saldo_ferias": 20,
  "banco_horas": 0.0,
  "regime": "hibrido"
}
```

### Checklist de validação do contrato do nó n8n

```
[ ] O nó retorna todos os campos ou apenas alguns?
[ ] saldo_ferias chega como número (20) ou string ("20")?
[ ] banco_horas com decimal chega como 15.5 ou "15.50"?
[ ] Quando funcionário não existe: retorna array vazio [] ou erro?
[ ] Quando nome tem acento (Eric Monné): busca funciona corretamente?
[ ] Case sensitive: "joão silva" encontra "João Silva"?
[ ] Funcionário com mesmo nome: retorna o primeiro ou todos?
```

### Teste de divergência: banco vs resposta do agente

```
CAMADA 1 — Banco MySQL
  João Silva → saldo_ferias = 20

CAMADA 2 — Nó MySQL do n8n
  Query retorna → {"saldo_ferias": 20}

CAMADA 3 — AI Agent (Cohere)
  Recebe contexto → "João tem 20 dias de férias"

CAMADA 4 — Resposta ao usuário
  "Você tem 20 dias de férias disponíveis" ✅

Se qualquer camada divergir → investigate com o diagrama acima
```

---

## Módulo 3 — Checklist pré e pós alteração na tabela

### Antes de qualquer UPDATE/INSERT na tabela funcionarios

```
[ ] Backup da tabela feito?
[ ] Query testada com SELECT antes de executar UPDATE/DELETE?
[ ] Quantidade de registros afetados verificada?
[ ] Rollback documentado?
[ ] Agente testado manualmente após alteração?
```

### Após alteração

```
[ ] Query 1.7 executada e resultado bate com o esperado?
[ ] Agente responde corretamente os dados alterados?
[ ] Dados anteriores não foram corrompidos?
[ ] Log de alteração registrado?
```

---

## Módulo 4 — Bug Reports de integridade de dados

### Template para bugs de dados encontrados

```markdown
## 🟠 Bug de Dados — [Título]

| Campo | Valor |
|-------|-------|
| **Tipo** | Dado inválido / Duplicata / Divergência agente×banco |
| **Tabela** | funcionarios |
| **Volume** | N registros afetados |
| **Ambiente** | Railway MySQL (staging/produção) |
| **Severidade** | P0 / P1 / P2 |

### Query que reproduz
```sql
[query aqui]
```

### Resultado obtido
[descrever]

### Resultado esperado
[descrever]

### Impacto no agente
[o agente responde dado errado? não encontra o funcionário? retorna dado de outro?]

### Ação sugerida
- [ ] Corrigir dado no banco (data fix)
- [ ] Corrigir query do nó n8n
- [ ] Adicionar constraint para prevenir repetição
- [ ] Re-testar agente após fix
```

---

> **"Dado correto na resposta do agente não garante dado correto no banco. Valide diretamente no MySQL."**

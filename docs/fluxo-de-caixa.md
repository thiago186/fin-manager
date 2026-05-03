# Fluxo de Caixa

> Documentação da feature de Fluxo de Caixa do FinManager  
> Última atualização: maio/2026

---

## 1. Visão Geral

A feature de **Fluxo de Caixa** permite que o usuário crie relatórios financeiros personalizados, agrupando categorias de transações da forma que preferir e acompanhando os valores mês a mês ao longo de um ano. É uma ferramenta flexível para montar demonstrativos como DRE (Demonstração do Resultado do Exercício), fluxo de caixa simplificado ou qualquer outro tipo de visão financeira customizada.

O usuário monta uma "visualização" definindo quais categorias entram em cada grupo e onde aparecem as linhas de resultado. O sistema calcula automaticamente os totais mensais e anuais, respeitando o sinal de receitas (positivo) e despesas (negativo).

---

## 2. Conceitos principais

| Termo | Significado |
|-------|-------------|
| **Visualização** | Configuração nomeada que define como o relatório será montado. Cada usuário pode ter várias visualizações (ex: "DRE Mensal", "Fluxo de Caixa Pessoal"). |
| **Grupo** | Conjunto de categorias que serão somadas juntas. Exemplos: "Receitas", "Despesas Fixas", "Custos Operacionais". |
| **Linha de Resultado** | Linha calculada automaticamente que soma todos os grupos posicionados acima dela. Exemplos: "Lucro Bruto", "Resultado Líquido". |
| **Posição** | Número que define a ordem de exibição dos grupos e resultados no relatório. Quanto menor o número, mais acima aparece. |
| **Transações sem categoria** | Transações que não possuem categoria ou cuja categoria não foi incluída em nenhum grupo. Aparecem em uma seção separada do relatório. |

---

## 3. Jornadas do usuário

### 3.1 Criar uma visualização de fluxo de caixa

1. O usuário acessa a página **Fluxo de Caixa** e clica em **"Nova Visualização"**.
2. Define um **nome** para a visualização (ex: "Minha DRE 2025").
3. Adiciona **grupos**, um por um:
   - Dá um nome ao grupo (ex: "Receitas").
   - Seleciona as **categorias** que pertencem a esse grupo.
4. Adiciona **linhas de resultado**, uma por uma:
   - Dá um nome ao resultado (ex: "Saldo do Período").
   - A ordem de criação define a posição no relatório.
5. Revisa a **ordem de exibição** na pré-visualização e, se estiver satisfeito, salva.

> **Arquivos envolvidos:**
> - Frontend: `frontend/pages/cash-flow/create.vue`, `frontend/composables/useCashFlowViews.ts`
> - Backend: `backend/src/apps/accounts/views/cash_flow_view.py`, `backend/src/apps/accounts/serializers/cash_flow_view.py`

### 3.2 Visualizar um relatório

1. O usuário está na lista de visualizações e clica em uma delas.
2. O sistema carrega o relatório para o **ano atual** por padrão.
3. O usuário pode:
   - Trocar o **ano** via dropdown.
   - Alternar o **escopo** entre "Todas" (todas as transações) ou "Parcelamentos" (apenas transações que fazem parte de parcelamentos).
   - Expandir ou recolher grupos para ver o detalhamento por categoria e subcategoria.
4. A tabela mostra 12 colunas de meses + total anual, com valores coloridos: verde para positivo, vermelho para negativo.
5. Transações sem categoria aparecem em uma tabela separada abaixo.

> **Arquivos envolvidos:**
> - Frontend: `frontend/pages/cash-flow/index.vue`, `frontend/composables/useCashFlowViews.ts`
> - Backend: `backend/src/apps/accounts/services/cash_flow_report_service.py` — método `generate_report`

### 3.3 Editar uma visualização

1. O usuário clica em **"Editar"** em uma visualização da lista.
2. O sistema carrega a configuração atual.
3. O usuário pode alterar nome, grupos, categorias e resultados.
4. Ao salvar, o sistema **substitui completamente** a configuração antiga pela nova.

> **Arquivos envolvidos:**
> - Frontend: `frontend/pages/cash-flow/edit/[id].vue`
> - Backend: `backend/src/apps/accounts/serializers/cash_flow_view.py` — método `update`

---

## 4. Regras de negócio

### 4.1 Como os valores são calculados

- **Receitas** (categorias do tipo `income`) entram como valores **positivos** no relatório.
- **Despesas** (categorias do tipo `expense`) entram como valores **negativos** no relatório.
- O total de um grupo é a soma de todas as transações das categorias incluídas naquele grupo, respeitando o sinal.
- O total anual é a soma dos 12 meses.

> **Exemplo prático:**  
> O grupo "Receitas" contém as categorias "Salário" e "Freelance". Em janeiro, o usuário teve R$ 5.000,00 de salário e R$ 1.200,00 de freelance. O grupo mostra R$ 6.200,00 em janeiro.  
> O grupo "Despesas Fixas" contém "Aluguel" e "Internet". Em janeiro, o usuário pagou R$ 1.500,00 de aluguel e R$ 150,00 de internet. O grupo mostra **-R$ 1.650,00** em janeiro.

### 4.2 Linhas de resultado

- Uma linha de resultado soma **todos os grupos que têm posição menor que a dela**.
- Isso permite criar demonstrativos em etapas: primeiro "Receitas", depois "Custos", depois um resultado "Lucro Bruto" que soma tudo o que está acima.
- Resultados não somam outros resultados, apenas grupos.

> **Exemplo prático:**  
> Posição 1: Grupo "Receitas"  
> Posição 2: Grupo "Custos"  
> Posição 3: Resultado "Lucro Bruto" → soma Receitas + Custos  
> Posição 4: Grupo "Despesas Operacionais"  
> Posição 5: Resultado "Lucro Líquido" → soma Receitas + Custos + Despesas Operacionais

### 4.3 Posições e ordenação

- Cada grupo e cada resultado possui uma **posição** (número inteiro).
- O relatório exibe os itens em ordem crescente de posição.
- **Não pode haver dois grupos ou resultados com a mesma posição** dentro da mesma visualização. O sistema valida isso e impede a criação/edição.

### 4.4 Escopo de transações

O relatório pode ser gerado em dois modos:

| Escopo | Descrição |
|--------|-----------|
| **Todas** | Inclui todas as transações do ano, independente de serem parcelamentos ou não. |
| **Parcelamentos** | Inclui **apenas** transações que fazem parte de um plano de parcelamento. Útil para analisar o impacto das parcelas no fluxo de caixa. |

### 4.5 Detalhamento por categoria e subcategoria

- Dentro de cada grupo, o usuário pode expandir para ver o detalhamento por **categoria**.
- Dentro de cada categoria, pode expandir novamente para ver o detalhamento por **subcategoria**.
- O sistema também mostra uma linha "Uncategorized" dentro de cada categoria para transações que não têm subcategoria.
- A porcentagem exibida ao lado de cada categoria/subcategoria representa a participação daquele item dentro do total do grupo ou categoria pai.

### 4.6 Transações sem categoria

- Transações que não possuem categoria atribuída, ou cuja categoria não foi incluída em nenhum grupo da visualização, aparecem em uma seção separada chamada **"Uncategorized"**.
- Isso garante que nenhum valor "suma" do relatório por engano.

### 4.7 Atualização da visualização

- Quando o usuário edita uma visualização, o sistema **apaga todos os grupos e resultados antigos** e recria com os novos dados.
- Isso significa que a edição é uma substituição completa, não um patch parcial.

---

## 5. Casos de uso típicos

### UC1: Demonstração de Resultado (DRE) pessoal
**Ator:** Usuário  
**Cenário:** Quer acompanhar seu resultado financeiro mensal no formato de uma DRE simplificada.  
**Ação:** Cria uma visualização com grupos "Receitas", "Despesas Fixas", "Despesas Variáveis" e resultados "Saldo Bruto" e "Saldo Líquido".  
**Resultado:** Consegue ver mês a mês se está sobrando ou faltando dinheiro, com o saldo líquido calculado automaticamente.

### UC2: Análise do impacto dos parcelamentos
**Ator:** Usuário  
**Cenário:** Quer entender quanto dos gastos mensais vêm de compras parceladas.  
**Ação:** Cria uma visualização com os grupos de despesa habituais e, ao gerar o relatório, alterna o escopo para **"Parcelamentos"**.  
**Resultado:** O relatório mostra apenas os valores das parcelas, permitindo comparar com o total de despesas no escopo "Todas".

### UC3: Controle de receitas vs despesas por área
**Ator:** Usuário  
**Cenário:** Quer separar despesas pessoais de despesas de trabalho.  
**Ação:** Cria uma visualização com grupos "Receitas", "Despesas Pessoais", "Despesas de Trabalho" e um resultado "Balanço Geral".  
**Resultado:** Visualiza de forma clara quanto gasta em cada área e qual o balanço final.

### UC4: Identificar transações esquecidas
**Ator:** Usuário  
**Cenário:** Notou que o relatório não bate com o saldo real.  
**Ação:** Gera o relatório e olha a seção **"Uncategorized"** no final.  
**Resultado:** Encontra transações que ficaram sem categoria ou cuja categoria não foi incluída em nenhum grupo, corrige o cadastro e gera o relatório novamente.

---

## 6. O que acontece "por trás" (resumo dos serviços)

Para quem precisar consultar o código, os principais pontos são:

- **`CashFlowReportService.generate_report`** — gera o relatório completo para uma visualização e ano. Calcula totais mensais por grupo, detalha categorias/subcategorias, calcula resultados e identifica transações sem categoria.
- **`CashFlowReportService._calculate_group_monthly_totals`** — soma as transações das categorias de um grupo, mês a mês, aplicando o sinal correto (receitas +, despesas -).
- **`CashFlowReportService._calculate_result_monthly_totals`** — soma todos os grupos com posição menor que a do resultado para produzir as linhas de resultado.
- **`CashFlowViewSerializer.update`** — ao editar uma visualização, deleta todos os grupos e resultados antigos e recria do zero com os novos dados.
- **`CashFlowViewViewSet.report`** — endpoint que expõe o relatório, aceitando `year` e `transaction_scope` como parâmetros.

---

## 7. Limites e observações

- O intervalo do relatório é sempre **um ano completo** (janeiro a dezembro). Não há suporte para períodos personalizados.
- O relatório agrupa por **mês calendário**, não por períodos contábeis customizados.
- Categorias podem ser usadas em **mais de um grupo** ao mesmo tempo, mas o sistema avisa se detectar que nem todas as categorias foram selecionadas ou se houver duplicatas.
- Subcategorias inativas (`is_active=false`) não aparecem no detalhamento.
- A ordem de exibição é definida pela **posição** numérica, não pela ordem de criação na tela (embora na prática o frontend atribua posições sequenciais).

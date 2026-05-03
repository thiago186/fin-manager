# Parcelamentos

> Documentação da feature de parcelamentos do FinManager  
> Última atualização: maio/2026

---

## 1. Visão Geral

A feature de **parcelamentos** permite que o usuário registre uma compra ou receita dividida em várias parcelas mensais, de forma automática. Em vez de criar 12 transações manualmente, por exemplo, o usuário preenche os dados uma única vez e o sistema gera todas as parcelas com datas e valores corretos.

Cada parcelamento vira um "plano" (`InstallmentPlan`) que agrupa as transações geradas. O usuário pode consultar esses planos em uma tela dedicada, expandir para ver as parcelas e, se necessário, excluir o plano inteiro de uma só vez.

---

## 2. Conceitos principais

| Termo | Significado |
|-------|-------------|
| **Plano de parcelamento** | O grupo que une todas as parcelas de uma mesma compra/receita. Guarda o valor total, valor de cada parcela, quantidade de parcelas e data da primeira. |
| **Parcela** | Cada transação individual gerada pelo plano. Possui um número sequencial (ex: 3 de 12) e uma data de vencimento. |
| **Grupo de parcelas** | Identificador único (`installment_group_id`) que liga as transações entre si. Serve para rastreabilidade. |
| **Modo de entrada** | Forma como o usuário informa os valores: pode digitar o **valor total + número de parcelas** ou o **valor de cada parcela + número de parcelas**. |

---

## 3. Jornadas do usuário

### 3.1 Criar um parcelamento (jornada feliz)

1. O usuário abre o modal de **Nova Transação**.
2. Preenche os campos comuns: tipo (despesa, receita ou transferência), descrição, data, conta/cartão e categoria.
3. Marca a opção **"Criar como parcelamento"**.
4. Escolhe o modo de entrada:
   - *Valor total + parcelas*: digita o valor integral da compra e em quantas vezes deseja dividir.
   - *Valor por parcela + parcelas*: digita quanto quer pagar por mês e o número de parcelas.
5. O sistema mostra uma prévia do parcelamento (ex: "12x de R$ 100,00 = R$ 1.200,00 a partir de 2024-01-15").
6. Ao salvar, o sistema cria o plano e gera todas as transações automaticamente, uma para cada mês.

> **Arquivos envolvidos:**
> - Frontend: `frontend/components/TransactionModal.vue`, `frontend/composables/useInstallmentPlans.ts`
> - Backend: `backend/src/apps/accounts/services/installment_service.py` — método `create_plan_with_transactions`

### 3.2 Visualizar parcelamentos

1. O usuário acessa a página **Parcelamentos**.
2. Vê uma lista com todos os planos criados, mostrando descrição, tipo, quantidade de parcelas, valor de cada uma, valor total e data de início.
3. Pode clicar em **"Ver parcelas"** para expandir um plano e ver a tabela com cada parcela (número, data, valor e categoria).
4. Se desejar, pode excluir um plano inteiro. O sistema remove o plano e **todas as suas transações** de uma só vez.

> **Arquivos envolvidos:**
> - Frontend: `frontend/pages/installments.vue`, `frontend/composables/useInstallmentPlans.ts`
> - Backend: `backend/src/apps/accounts/views/installment_plan.py` — endpoints de listagem, detalhe e exclusão

### 3.3 Editar uma parcela (com impacto no plano inteiro)

1. O usuário edita uma transação que faz parte de um parcelamento.
2. O sistema exibe um aviso: *"Esta transação faz parte de um parcelamento. Alterações no valor, número de parcelas, data ou conta/categoria afetarão todas as parcelas."*
3. Ao salvar, o sistema propaga as alterações para **todas as parcelas do mesmo plano**.

> **Arquivos envolvidos:**
> - Frontend: `frontend/components/TransactionModal.vue`
> - Backend: `backend/src/apps/accounts/views/transaction.py` — método `_update_with_plan_sync`
> - Backend: `backend/src/apps/accounts/services/installment_update_service.py` — classe `InstallmentUpdateService`

---

## 4. Regras de negócio

### 4.1 Cálculo dos valores

- O sistema aceita **dois modos de entrada**:
  - **Valor total**: divide o total pelo número de parcelas. Se houver centavos que não dividem igualmente, a diferença de arredondamento é absorvida pela **primeira parcela**.
  - **Valor por parcela**: multiplica o valor informado pelo número de parcelas para obter o total.

> **Exemplo prático:**  
> Compra de R$ 100,00 em 3x. Cada parcela base seria R$ 33,33. Como 33,33 × 3 = 99,99, falta R$ 0,01. A primeira parcela fica R$ 33,34 e as demais R$ 33,33.

### 4.2 Geração das datas

- As parcelas são sempre mensais, com intervalo de 1 mês entre cada uma.
- A primeira parcela usa a data informada pelo usuário. A segunda é 1 mês depois, a terceira 2 meses depois, e assim por diante.
- O dia da data é preservado (ex: se a primeira é dia 15, todas serão dia 15).

### 4.3 Alterações em cascata

Quando o usuário edita uma parcela que pertence a um plano, o sistema propaga algumas mudanças para **todas as parcelas** e outras não:

| Campo alterado | Comportamento |
|----------------|---------------|
| **Valor** | Altera o valor de **todas** as parcelas e recalcula o total do plano. |
| **Número de parcelas** | Cria novas parcelas (se aumentou) ou remove as excedentes (se diminuiu). Atualiza o total do plano. |
| **Data** | Muda a data da parcela editada e **desloca todas as subsequentes** mantendo o intervalo mensal. Parcelas anteriores não mudam. |
| **Conta / Cartão / Categoria / Subcategoria / Tipo** | Aplica em **todas** as parcelas do plano. |
| **Descrição / Tags** | **Não** são propagadas. Cada parcela mantém sua própria descrição e tags. |

> **Exemplo prático de mudança de data:**  
> O usuário muda a parcela 5 de 15/01 para 10/07. As parcelas 6, 7, 8... também deslocam para o dia 10, mantendo os meses subsequentes (10/08, 10/09...). As parcelas 1 a 4 permanecem em janeiro, fevereiro, março e abril.

### 4.4 Exclusão

- Excluir um plano de parcelamento **remove todas as transações vinculadas** automaticamente.
- Não é possível excluir uma única parcela de um plano pela tela de parcelamentos — a exclusão é sempre do plano inteiro.

### 4.5 Validações

- Não é permitido informar ao mesmo tempo uma **conta bancária** e um **cartão de crédito** no mesmo parcelamento.
- O número de parcelas deve ser entre **2 e 360**.
- A parcela atual nunca pode ser maior que o total de parcelas.
- Não é possível alterar o número da parcela individual (ex: mudar a parcela 3 para parcela 5) se ela faz parte de um plano.

---

## 5. Casos de uso típicos

### UC1: Compra parcelada no cartão de crédito
**Ator:** Usuário  
**Cenário:** Comprou um celular de R$ 3.600,00 em 12x no cartão.  
**Ação:** Cria uma despesa parcelada, vincula ao cartão de crédito, informa o valor total e 12 parcelas.  
**Resultado:** O sistema gera 12 transações de R$ 300,00, uma para cada mês, todas vinculadas ao mesmo cartão.

### UC2: Aumentar o número de parcelas depois
**Ator:** Usuário  
**Cenário:** Comprou algo em 6x, mas depois decidiu alongar para 10x.  
**Ação:** Edita qualquer parcela do plano e muda o campo "Total de Parcelas" de 6 para 10.  
**Resultado:** O sistema cria as 4 parcelas faltantes, mantendo o mesmo valor mensal e o intervalo de datas. O total do plano é recalculado.

### UC3: Corrigir a conta de um parcelamento inteiro
**Ator:** Usuário  
**Cenário:** Cadastrou um parcelamento na conta errada.  
**Ação:** Edita uma parcela qualquer e troca a conta.  
**Resultado:** Todas as parcelas do plano são movidas para a nova conta automaticamente.

### UC4: Excluir um parcelamento cancelado
**Ator:** Usuário  
**Cenário:** Cancelou a compra e precisa remover todo o rastro do parcelamento.  
**Ação:** Vai na página de Parcelamentos, encontra o plano e clica em excluir.  
**Resultado:** O plano e todas as suas transações são removidos do extrato.

---

## 6. O que acontece "por trás" (resumo dos serviços)

Para quem precisar consultar o código, os principais pontos são:

- **`InstallmentService.create_plan_with_transactions`** — cria o plano e gera as transações de forma atômica (tudo ou nada).
- **`InstallmentUpdateService.update_plan_from_transaction`** — sincroniza o plano inteiro quando o usuário edita uma parcela. Decide se precisa criar, remover, recalcular valores ou deslocar datas.
- **`TransactionViewSet._update_with_plan_sync`** — intercepta a atualização de uma transação e, se ela pertencer a um plano, aciona o serviço de sincronização.
- **`InstallmentPlanViewSet`** — expõe a API de criação, listagem, detalhe e exclusão dos planos.

---

## 7. Limites e observações

- O intervalo entre parcelas é sempre **mensal** (não há suporte para quinzenal, semanal etc.).
- A data da primeira parcela define o "dia fixo" de todas as outras.
- A edição em cascata afeta **todas** as parcelas do plano; não há como editar apenas uma parcela isoladamente sem desvinculá-la do plano.
- Descrições e tags são tratadas como dados individuais de cada parcela, não do plano.

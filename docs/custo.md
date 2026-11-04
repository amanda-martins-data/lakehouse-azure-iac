# Custo

Este documento nao traz precos: eles mudam por regiao e com o tempo. A
referencia e a [calculadora do Azure](https://azure.microsoft.com/pricing/calculator/)
para a regiao escolhida (padrao: `brazilsouth`).

## O que custa e quando

| Recurso | Cobra por | Com o lake parado |
|---|---|---|
| Storage (ADLS Gen2, LRS) | GB armazenado e transacoes | centavos para o volume deste projeto |
| Workspace Databricks Premium | DBU consumida por cluster | zero sem cluster ligado |
| Cluster do job (single node) | VM + DBU por minuto ligado | zero: so liga quando o job roda, e o agendamento nasce pausado |
| Key Vault (standard) | operacoes | praticamente zero |
| Log Analytics | GB ingerido | limitado por `log_daily_quota_gb` (padrao 1 GB/dia) |
| Access connector, Unity Catalog | - | sem cobranca propria |

O custo fixo sem compute fica perto de zero. O custo real aparece
quando um cluster liga.

## Controles no codigo

- `azurerm_consumption_budget_resource_group` com alerta em 50% do gasto
  real e 100% do previsto (`monthly_budget`, padrao 10 na moeda da
  assinatura).
- Job com cluster single node, criado por execucao e destruido ao final.
- Agendamento `PAUSED`: nada roda sem decisao explicita.
- Ciclo de vida: bronze vai para a camada fria apos
  `bronze_cool_after_days` (padrao 30).
- Cota diaria no Log Analytics.

## Destruir tudo

```bash
terraform -chdir=infra/envs/dev/catalog destroy
terraform -chdir=infra/envs/dev/platform destroy
```

O resource group tem `prevent_deletion_if_contains_resources = true`: se
algo foi criado fora do Terraform dentro dele, o destroy para e avisa em
vez de apagar.

O Key Vault tem purge protection: apos o destroy ele fica em soft delete
por 90 dias e o nome nao pode ser reutilizado nesse periodo (por isso o
nome leva um sufixo aleatorio).

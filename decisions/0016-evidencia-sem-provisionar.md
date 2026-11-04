# 0016 - Duas raizes de Terraform e niveis de evidencia

**Status:** aceita

## Contexto

Dois problemas diferentes:

1. O provider do Databricks precisa da URL de um workspace que ja exista
   para planejar. Numa raiz unica, o primeiro `plan` falha.
2. Rodar o lakehouse completo no Azure tem custo (cluster), e a conta
   gratuita do Azure nao cria clusters do Databricks. Mesmo assim, o
   repositorio precisa mostrar que o codigo funciona, nao so que existe.

## Decisao

**Duas raizes**: `infra/envs/dev/platform` (Azure Resource Manager) e
`infra/envs/dev/catalog` (Databricks/Unity Catalog), que recebe as saidas
da primeira por variaveis.

**Evidencia em niveis**, cada um registrado no README com o que foi e o
que nao foi executado:

| Nivel | O que prova | Custo |
|---|---|---|
| 1 - CI | fmt, validate das duas raizes, tflint, checkov; pipeline testado em Delta e Parquet | zero |
| 1b - dados reais | o pipeline inteiro sobre arquivos reais do INMET e do IBGE (workflow manual) | zero |
| 2 - plan | plano da plataforma contra uma assinatura real | zero |
| 3 - apply/destroy da plataforma | storage, workspace, connector, Key Vault, logs e budget criados e destruidos | centavos (sem cluster) |
| 4 - ponta a ponta no Azure | catalogo, job e cluster | pago (pay-as-you-go) |

## Consequencias

- O estado de cada nivel fica explicito, sem sugerir mais do que foi feito.
- O job do Databricks e definido no Terraform, mas so roda no nivel 4.

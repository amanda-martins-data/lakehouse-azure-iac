# 0013 - Delta Lake como formato das tabelas

**Status:** aceita

## Contexto

As tres camadas precisam de escrita idempotente: reprocessar um arquivo
do INMET nao pode duplicar linhas, e a gold precisa de upsert pela chave
(municipio, data). As opcoes avaliadas foram Delta Lake, Apache Iceberg
e Parquet puro.

## Decisao

Delta Lake em todas as camadas.

- E o formato nativo do Databricks e do Unity Catalog: nenhuma
  configuracao extra no cluster.
- `replaceWhere` resolve a bronze (substituir so as linhas de um
  arquivo) e `MERGE` resolve a gold, ambos atomicos.
- O mesmo codigo roda localmente com `delta-spark`, entao o CI testa o
  caminho de producao.

## Consequencias

- Iceberg seria a escolha se o lake precisasse ser lido por varios
  motores (Trino, Snowflake) sem o Databricks no meio. Nao e o caso aqui.
- O pacote tem um modo Parquet (`LAKEHOUSE_FORMAT=parquet`) so para
  ambientes onde os jars do Delta nao podem ser baixados. Ele emula
  replaceWhere com overwrite dinamico de particao e MERGE com
  anti-join + uniao. O CI roda os testes nos dois modos; producao e
  sempre Delta.

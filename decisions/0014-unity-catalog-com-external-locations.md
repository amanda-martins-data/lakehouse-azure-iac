# 0014 - Unity Catalog com external locations, sem mounts

**Status:** aceita

## Contexto

Ha duas formas de o Databricks acessar o ADLS: montar containers no
DBFS (`dbutils.fs.mount`) com uma credencial, ou registrar o storage no
Unity Catalog como storage credential + external locations.

## Decisao

Unity Catalog. A camada `infra/envs/dev/catalog` cria:

- uma storage credential baseada na identidade gerenciada do access
  connector (ADR 0015);
- uma external location por camada (`bronze`, `silver`, `gold`,
  `managed`);
- o catalogo `lakehouse_dev`, com um schema por camada e `storage_root`
  apontando para a external location correspondente;
- grants: engenharia escreve em bronze e silver; analistas so leem a
  gold.

## Consequencias

- Mounts ficam visiveis para todo usuario do workspace, sem controle por
  tabela. Com UC, o acesso e por grant e fica auditado.
- A Databricks trata mounts como padrao legado e recomenda Unity Catalog.
- Exige workspace Premium, o que esta no modulo `databricks`.
- Os jobs registram as tabelas como externas (`CREATE TABLE ... LOCATION`)
  so quando recebem `--catalog`; localmente, escrevem apenas os arquivos.

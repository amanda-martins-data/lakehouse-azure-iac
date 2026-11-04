# 0017 - Sem VNet injection nem private endpoints nesta versao

**Status:** aceita (revisar antes de qualquer uso com dado sensivel)

## Contexto

O padrao de producao para Databricks no Azure inclui VNet injection,
Private Link e private endpoints para storage e Key Vault. Isso
multiplica recursos (VNet, subnets, NSGs, zonas de DNS privado) e custo,
e nao muda nada na logica do lakehouse.

## Decisao

Nesta versao, o isolamento e por identidade, nao por rede:

- storage e Key Vault com acesso publico de rede, mas sem chave
  compartilhada e com RBAC (ADR 0015);
- workspace com secure cluster connectivity (`no_public_ip = true`): os
  nos do cluster nao recebem IP publico;
- auditoria de leitura, escrita e exclusao de blobs e de acesso ao Key
  Vault no Log Analytics.

As regras do checkov que exigem rede privada ou chave gerenciada pelo
cliente estao suprimidas no codigo, uma a uma, com o motivo.

## Consequencias

- Adequado para dados publicos (INMET, IBGE), que e o caso.
- Para dado sensivel, o proximo passo e um modulo `network` com VNet
  injection e private endpoints; as supressoes do checkov viram a lista
  do que precisa ser resolvido.

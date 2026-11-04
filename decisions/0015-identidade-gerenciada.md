# 0015 - Identidade gerenciada, nenhuma chave de storage

**Status:** aceita

## Contexto

O Unity Catalog precisa de uma identidade para ler e gravar no ADLS. As
opcoes sao a chave da conta, um service principal com segredo, ou a
identidade gerenciada de um access connector.

## Decisao

Identidade gerenciada (system-assigned) do `azurerm_databricks_access_connector`,
com o papel `Storage Blob Data Contributor` na conta do lake.

Complementos que fecham a porta da chave:

- `shared_access_key_enabled = false` e `local_user_enabled = false` na conta;
- `default_to_oauth_authentication = true`;
- o provider `azurerm` usa `storage_use_azuread = true`, e quem roda o
  Terraform recebe `Storage Blob Data Owner` no resource group para criar
  os filesystems sem chave.

## Consequencias

- Nao ha segredo para rotacionar, vazar ou guardar no Key Vault.
- O Key Vault continua no projeto para segredos que nao tenham
  alternativa por identidade (por exemplo, credencial de uma API externa).
- Desligar a chave compartilhada quebra ferramentas que dependem dela
  (algumas versoes do Storage Explorer). Elas precisam usar login do Entra ID.

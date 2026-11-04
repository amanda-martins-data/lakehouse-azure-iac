variable "workspace_url" {
  description = "URL do workspace (saida workspace_url de ../platform), sem https://."
  type        = string
}

variable "workspace_numeric_id" {
  description = "ID numerico do workspace. So e usado quando metastore_id e informado."
  type        = number
  default     = null
}

variable "metastore_id" {
  description = "Metastore a atribuir ao workspace. Workspaces novos costumam receber o metastore da regiao automaticamente; nesse caso, deixe null."
  type        = string
  default     = null
}

variable "access_connector_id" {
  description = "Access connector do Unity Catalog (saida access_connector_id de ../platform)."
  type        = string
}

variable "storage_account_name" {
  description = "Conta de storage do lake (saida storage_account_name de ../platform)."
  type        = string
}

variable "catalog_name" {
  description = "Nome do catalogo."
  type        = string
  default     = "lakehouse_dev"
}

variable "data_engineers_group" {
  description = "Grupo de conta do Databricks com escrita nas camadas."
  type        = string
  default     = "data-engineers"
}

variable "data_analysts_group" {
  description = "Grupo de conta do Databricks com leitura da camada gold."
  type        = string
  default     = "data-analysts"
}

variable "repo_url" {
  description = "Repositorio Git de onde o job le o codigo."
  type        = string
  default     = "https://github.com/amanda-martins-data/lakehouse-azure-iac"
}

variable "repo_branch" {
  description = "Branch usada pelo job."
  type        = string
  default     = "main"
}

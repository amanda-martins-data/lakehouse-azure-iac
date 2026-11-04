variable "workspace_name" {
  description = "Nome do workspace do Azure Databricks."
  type        = string
}

variable "managed_resource_group_name" {
  description = "Resource group gerenciado pelo Databricks (criado por ele)."
  type        = string
}

variable "access_connector_name" {
  description = "Nome do access connector usado pelo Unity Catalog."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group dos recursos."
  type        = string
}

variable "location" {
  description = "Regiao do Azure."
  type        = string
}

variable "tags" {
  description = "Tags aplicadas a todos os recursos."
  type        = map(string)
  default     = {}
}

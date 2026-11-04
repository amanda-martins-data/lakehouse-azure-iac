variable "key_vault_name" {
  description = "Nome do Key Vault (3 a 24 caracteres, unico no Azure)."
  type        = string
}

variable "log_analytics_name" {
  description = "Nome do workspace do Log Analytics."
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

variable "tenant_id" {
  description = "Tenant do Entra ID que autentica no Key Vault."
  type        = string
}

variable "storage_account_id" {
  description = "Conta de storage do lake, para os logs de acesso a blobs."
  type        = string
}

variable "log_retention_days" {
  description = "Retencao dos logs, em dias."
  type        = number
  default     = 30
}

variable "log_daily_quota_gb" {
  description = "Teto diario de ingestao no Log Analytics, em GB. Limita o custo em dev."
  type        = number
  default     = 1
}

variable "tags" {
  description = "Tags aplicadas a todos os recursos."
  type        = map(string)
  default     = {}
}

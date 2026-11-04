variable "subscription_id" {
  description = "Assinatura do Azure onde o ambiente sera criado."
  type        = string
}

variable "prefix" {
  description = "Prefixo curto dos nomes (minusculas e numeros)."
  type        = string
  default     = "lkh"

  validation {
    condition     = can(regex("^[a-z0-9]{2,6}$", var.prefix))
    error_message = "Use de 2 a 6 caracteres, apenas minusculas e numeros."
  }
}

variable "location" {
  description = "Regiao do Azure."
  type        = string
  default     = "brazilsouth"
}

variable "monthly_budget" {
  description = "Teto mensal do resource group, na moeda da assinatura."
  type        = number
  default     = 10
}

variable "budget_start_date" {
  description = "Inicio do orcamento: primeiro dia de um mes, em RFC3339."
  type        = string
  default     = "2026-11-01T00:00:00Z"
}

variable "alert_emails" {
  description = "E-mails que recebem os alertas de orcamento."
  type        = list(string)
}

variable "tags" {
  description = "Tags extras aplicadas a todos os recursos."
  type        = map(string)
  default     = {}
}

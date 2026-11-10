variable "jwt_secret" {
  type        = string
  description = "Secret value for use in generating a JWT token"
  sensitive   = true
}

variable "jwt_expiry_minutes" {
  type        = string
  description = "JWT token expiry duration in minutes"
  sensitive   = true
}

variable "jwt_algorithm" {
  type        = string
  description = "JWT token creation algorithm"
}

variable "environment" {
  type = "string"
  description = "Deployment environment"

  validation {
    condition = contains(["staging", "production"], var.environment)
    error_message = "environment must be staging or production"
  }
}
# Variables for Development Environment

variable "aws_region" {
  description = "AWS region for development environment"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "node_count" {
  description = "Number of worker nodes"
  type        = number
  default     = 3
}

variable "node_count_min" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 3
}

variable "node_count_max" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 6
}

variable "instance_type" {
  description = "EC2 instance type for worker nodes"
  type        = string
  default     = "m5.xlarge"  # Dev: smaller instances
}

variable "public_access_cidrs" {
  description = "CIDR blocks allowed to access cluster API"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Dev: open access (restrict in prod)
}
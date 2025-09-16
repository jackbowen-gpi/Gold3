# Azure Cost Analysis for GOLD3 Development Server

## Overview

This document provides a detailed cost analysis for running the GOLD3 development server on Azure with **partial usage patterns**. The server will be operational **8 hours per day, 5 days per week** (40 hours/week) rather than 24/7, significantly reducing costs.

## Key Assumptions

### Usage Pattern

- **Operational Hours**: 8 hours/day, 5 days/week (40 hours/week)
- **Monthly Operational Hours**: ~160-170 hours/month
- **Environment**: Development server (not production)
- **Security**: All security features enabled
- **External Access**: None (internal development only)

### Architecture Components

- **Azure Container Apps**: Django web application + MediaWiki
- **Azure Database for PostgreSQL**: Primary database
- **Azure Cache for Redis**: Caching and message broker
- **Azure Container Registry**: Private container registry

## Detailed Cost Breakdown

### 1. Azure Container Apps

**Configuration:**

- Web App: 0.5 CPU cores, 1GB RAM, 1-3 instances
- Wiki: 0.25 CPU cores, 0.5GB RAM, 1 instance
- Environment: Azure Container App Environment

**Pricing (Pay-as-you-go):**

- Base price per second: $0.000008/vCPU/second + $0.00000016/GB/second
- Monthly cost calculation: (vCPU-seconds × $0.000008) + (GB-seconds × $0.00000016)

**Estimated Monthly Cost (160 hours):**

- Web App: ~$8-12/month
- Wiki: ~$2-3/month
- **Subtotal**: **$10-15/month**

### 2. Azure Database for PostgreSQL

**Configuration:**

- Tier: Burstable (B1ms)
- Storage: 32GB
- Backup: 7 days retention

**Pricing:**

- Compute: $0.0138/hour (B1ms)
- Storage: $0.115/GB/month
- Backup: Included in compute

**Estimated Monthly Cost (160 hours):**

- Compute: $0.0138 × 160 hours = $2.21
- Storage: 32GB × $0.115 = $3.68
- **Subtotal**: **$5.89/month**

### 3. Azure Cache for Redis

**Configuration:**

- Tier: Basic C0 (250MB)
- No clustering

**Pricing:**

- Basic C0: $0.022/hour

**Estimated Monthly Cost (160 hours):**

- Redis: $0.022 × 160 hours = $3.52
- **Subtotal**: **$3.52/month**

### 4. Azure Container Registry

**Configuration:**

- Tier: Basic
- Storage: Minimal (2-3 images)

**Pricing:**

- Basic tier: $0.167/day (first 100GB)
- Storage: $0.10/GB/month

**Estimated Monthly Cost:**

- Registry: $0.167 × ~20 operational days = $3.34
- Storage: Negligible (< $0.50)
- **Subtotal**: **$3.84/month**

## Total Monthly Cost Summary

| Service                       | Monthly Cost     | Percentage |
| ----------------------------- | ---------------- | ---------- |
| Azure Container Apps          | $10-15           | 45-50%     |
| Azure Database for PostgreSQL | $6               | 20-25%     |
| Azure Cache for Redis         | $4               | 15-20%     |
| Azure Container Registry      | $4               | 15-20%     |
| **Total**                     | **$24-29/month** | **100%**   |

## Cost Optimization Strategies

### 1. Usage-Based Scaling

- **Auto-scaling**: Container Apps scale to 0 when not in use
- **Database**: Can be paused when not needed
- **Redis**: Can be stopped when not needed

### 2. Reserved Instances (Optional)

- **1-year reservation**: 20-30% savings
- **3-year reservation**: 40-50% savings
- **Not recommended for dev environments**

### 3. Development-Specific Optimizations

- **Lower resource allocation**: Using minimal CPU/memory for dev
- **Single instance**: No high availability needed for dev
- **Basic tiers**: Sufficient for development workloads

## Security Features Included

### Network Security

- **Azure Virtual Network**: Isolated network environment
- **Private endpoints**: Secure database connections
- **Firewall rules**: Restrict access to authorized IPs only
- **No public internet exposure**: Development server only

### Application Security

- **Azure Container Registry**: Private registry with authentication
- **Container scanning**: Security vulnerability scanning
- **RBAC**: Role-based access control
- **Azure Monitor**: Security monitoring and alerting

### Data Security

- **Encryption at rest**: All data encrypted
- **Encryption in transit**: TLS 1.2+ required
- **Backup encryption**: Secure backup storage
- **Database security**: PostgreSQL security features

## Cost Comparison

### Traditional Hosting vs Azure

| Aspect           | Traditional VPS | Azure Container Apps |
| ---------------- | --------------- | -------------------- |
| **Setup Time**   | 2-4 hours       | 15-30 minutes        |
| **Monthly Cost** | $50-100         | $24-29               |
| **Scaling**      | Manual          | Automatic            |
| **Security**     | Self-managed    | Enterprise-grade     |
| **Maintenance**  | Self-managed    | Azure-managed        |

### 24/7 vs Partial Usage

| Usage Pattern       | Monthly Cost | Savings            |
| ------------------- | ------------ | ------------------ |
| 24/7 operation      | $60-75       | -                  |
| 8h/day, 5 days/week | $24-29       | **60-65% savings** |
| 4h/day, 5 days/week | $12-15       | **75-80% savings** |

## Monitoring and Cost Control

### Azure Cost Management

- **Cost alerts**: Set up budget alerts
- **Resource tagging**: Tag all resources for cost tracking
- **Cost analysis**: Monthly cost reports
- **Usage optimization**: Identify unused resources

### Development Workflow

- **Start/Stop automation**: Scripts to start/stop resources
- **Cost monitoring**: Daily cost tracking
- **Resource cleanup**: Remove unused resources
- **Budget limits**: Set monthly spending limits

## Recommendations

### For Development Teams

1. **Use partial hours**: Significant cost savings vs 24/7
2. **Monitor usage**: Track actual vs estimated costs
3. **Clean up regularly**: Remove unused resources
4. **Use basic tiers**: Sufficient for development

### Cost-Saving Tips

1. **Scale to zero**: Configure auto-scaling to zero instances
2. **Database pausing**: Pause database when not in use
3. **Resource scheduling**: Use Azure Automation for start/stop
4. **Cost alerts**: Set up alerts at 80% of budget

## Conclusion

The GOLD3 development server on Azure offers **excellent value** with:

- **$24-29/month** for partial usage (8h/day, 5 days/week)
- **60-65% cost savings** compared to 24/7 operation
- **Enterprise-grade security** with no external exposure
- **Automatic scaling** and management
- **Professional development environment**

This cost structure makes Azure an ideal platform for development teams requiring a secure, scalable, and cost-effective development environment.

---

_Last updated: September 16, 2025_
_Cost estimates based on Azure Pay-as-you-go pricing (East US region)_
_Actual costs may vary based on usage patterns and Azure pricing changes_

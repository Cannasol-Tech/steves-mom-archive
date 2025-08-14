# Azure SKU Selection Guide

## Overview

This document defines the selected SKUs (Stock Keeping Units) for each Azure service in the Steve's Mom AI Chatbot project, optimized for MVP cost constraints while maintaining necessary functionality.

## Cost Optimization Strategy

**Primary Goal**: Minimize costs for MVP while ensuring:
- Adequate performance for initial user load (10-20 employees)
- Ability to scale when needed
- Production-ready reliability
- Compliance with security requirements

## Service SKU Selections

### 1. Azure Functions

#### Selected SKU: Consumption Plan (Y1)
**Rationale**: Pay-per-execution model ideal for MVP with unpredictable traffic

**Specifications**:
- **SKU Code**: `Y1`
- **Pricing Model**: Pay-per-execution + memory consumption
- **Memory**: 128MB - 1.5GB per execution
- **Timeout**: 5 minutes (default), 10 minutes (max)
- **Concurrent Executions**: 200 per instance
- **Cold Start**: Yes (acceptable for MVP)

**Cost Estimate**:
- **Free Tier**: 1M executions + 400,000 GB-s per month
- **Paid Tier**: $0.000016 per execution + $0.000016 per GB-s
- **Expected Monthly Cost**: $0-50 (within free tier for MVP)

**Alternative**: Flex Consumption (FC1)
- **When to Consider**: If cold starts become problematic
- **Additional Cost**: ~$20-40/month for always-ready instances

### 2. Azure SQL Database

#### Selected SKU: Basic (B)
**Rationale**: Sufficient for MVP data storage with cost optimization

**Specifications**:
- **SKU Code**: `Basic`
- **DTU**: 5 DTUs
- **Storage**: 2GB included
- **Max Database Size**: 2GB
- **Backup Retention**: 7 days
- **Point-in-time Restore**: Yes

**Cost Estimate**:
- **Monthly Cost**: ~$5/month
- **Storage Overage**: $0.10/GB/month if exceeding 2GB

**Upgrade Path**:
- **Standard S0**: 10 DTUs, 250GB - $15/month
- **Standard S1**: 20 DTUs, 250GB - $30/month

### 3. Azure Cache for Redis

#### Selected SKU: Basic C0
**Rationale**: Minimal caching needs for MVP session management

**Specifications**:
- **SKU Code**: `Basic_C0`
- **Memory**: 250MB
- **Connections**: 256
- **Bandwidth**: Low
- **SLA**: None (Basic tier)
- **Replication**: No

**Cost Estimate**:
- **Monthly Cost**: ~$16/month

**Upgrade Path**:
- **Standard C0**: Same specs + SLA + replication - $32/month
- **Standard C1**: 1GB memory - $62/month

### 4. Azure Storage Account

#### Selected SKU: Standard LRS
**Rationale**: Local redundancy sufficient for MVP, lowest cost option

**Specifications**:
- **SKU Code**: `Standard_LRS`
- **Replication**: Locally Redundant Storage
- **Durability**: 99.999999999% (11 9's)
- **Availability**: 99.9%
- **Performance Tier**: Standard

**Cost Estimate**:
- **Hot Tier**: $0.0184/GB/month
- **Cool Tier**: $0.01/GB/month
- **Archive Tier**: $0.00099/GB/month
- **Transactions**: $0.0004 per 10,000 transactions

**Upgrade Path**:
- **Standard GRS**: Geographic redundancy - 2x cost
- **Premium LRS**: Higher performance - 3x cost

### 5. Azure Key Vault

#### Selected SKU: Standard
**Rationale**: Basic secret management, no HSM requirements for MVP

**Specifications**:
- **SKU Code**: `Standard`
- **Operations**: $0.03 per 10,000 operations
- **Secrets**: Unlimited
- **Keys**: Software-protected
- **Certificates**: Supported

**Cost Estimate**:
- **Monthly Cost**: $0-5 (based on operations)
- **Certificate Operations**: $3 per certificate operation

**Alternative**: Premium
- **When to Consider**: If HSM-backed keys required
- **Additional Cost**: $1/key/month

### 6. Application Insights

#### Selected SKU: Pay-as-you-go
**Rationale**: Usage-based pricing aligns with MVP traffic patterns

**Specifications**:
- **Data Ingestion**: $2.30/GB after 5GB free
- **Data Retention**: 90 days included
- **Extended Retention**: $0.10/GB/month
- **Web Tests**: $1 per test per month

**Cost Estimate**:
- **Monthly Cost**: $0-20 (within free tier for MVP)

### 7. Log Analytics Workspace

#### Selected SKU: Pay-as-you-go
**Rationale**: Minimal logging needs for MVP

**Specifications**:
- **Data Ingestion**: $2.30/GB after 5GB free
- **Data Retention**: 31 days included
- **Extended Retention**: $0.10/GB/month

**Cost Estimate**:
- **Monthly Cost**: $0-10 (within free tier for MVP)

## Total Cost Estimation

### MVP Monthly Costs (USD)

| Service | SKU | Estimated Cost |
|---------|-----|----------------|
| Azure Functions | Consumption (Y1) | $0-50 |
| SQL Database | Basic | $5 |
| Redis Cache | Basic C0 | $16 |
| Storage Account | Standard LRS | $5-15 |
| Key Vault | Standard | $0-5 |
| Application Insights | Pay-as-you-go | $0-20 |
| Log Analytics | Pay-as-you-go | $0-10 |
| **Total** | | **$26-121** |

### Cost Optimization Recommendations

1. **Monitor Usage**: Set up cost alerts at $50, $100, $150
2. **Right-size Early**: Review usage after 30 days
3. **Leverage Free Tiers**: Maximize free tier utilization
4. **Reserved Instances**: Consider for predictable workloads after MVP

## Scaling Considerations

### Performance Thresholds
- **Functions**: Monitor execution time and cold starts
- **SQL Database**: Monitor DTU utilization (>80% = upgrade)
- **Redis**: Monitor memory usage (>80% = upgrade)
- **Storage**: Monitor transaction rates and latency

### Upgrade Triggers
- **User Growth**: >50 concurrent users
- **Performance Issues**: Response time >2 seconds
- **Reliability Requirements**: Need for SLAs
- **Compliance**: Data residency or encryption requirements

## Environment-Specific Variations

### Development Environment
- **Functions**: Consumption (same)
- **SQL Database**: Basic (same)
- **Redis**: Basic C0 (same)
- **Storage**: Standard LRS (same)
- **Estimated Cost**: $20-80/month

### Staging Environment
- **Functions**: Consumption (same)
- **SQL Database**: Standard S0 (upgrade for testing)
- **Redis**: Standard C0 (upgrade for SLA testing)
- **Storage**: Standard LRS (same)
- **Estimated Cost**: $40-100/month

### Production Environment
- **Functions**: Consumption → Flex Consumption (if needed)
- **SQL Database**: Basic → Standard S1 (if needed)
- **Redis**: Basic C0 → Standard C1 (if needed)
- **Storage**: Standard LRS → Standard GRS (if needed)
- **Estimated Cost**: $50-200/month

## Monitoring and Alerting

### Cost Alerts
- **Budget Alert**: $100/month (80% of expected max)
- **Anomaly Detection**: 20% increase over baseline
- **Service-Specific**: Individual service thresholds

### Performance Monitoring
- **Functions**: Execution duration, failure rate
- **SQL Database**: DTU percentage, connection count
- **Redis**: Memory usage, hit rate
- **Storage**: Availability, latency

## Review Schedule

- **Weekly**: Cost and usage review during MVP
- **Monthly**: Performance and scaling assessment
- **Quarterly**: SKU optimization review
- **Annually**: Reserved instance evaluation

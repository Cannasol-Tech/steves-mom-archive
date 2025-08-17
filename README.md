# Steve's Mom AI Chatbot (MVP)

AI-powered chatbot with Azure Functions backend, React frontend, and comprehensive business automation tools.

## 🚀 Quick Start

### Development Setup

```bash
# Complete project setup
make setup

# Start development servers
make preview

# Run tests
make test-unit
```

## 📋 Make Targets (Standardized Workflow)

### Testing

- `make test` - Run all tests (unit + integration + acceptance)
- `make test-unit` - Run unit tests only
- `make test-integration` - Run integration tests
- `make test-acceptance` - Run acceptance tests (behave)
- `make test-frontend` - Run frontend tests (Jest/React Testing Library)
- `make test-infra` - Run infrastructure tests (Bicep validation)

### Development

- `make setup` - Complete project setup (backend + frontend + dev deps)
- `make preview` - Start dev servers (backend + frontend)
- `make dev` - Start development environment with hot reload
- `make clean` - Clean build artifacts and caches

### Code Quality

- `make lint` - Run all linters (Python, JS, Markdown)
- `make fix-lint` - Auto-fix linting issues where possible

### Deployment

- `make deploy` - Deploy full application (infra + functions)
- `make deploy-infra` - Deploy infrastructure only (Bicep)
- `make deploy-functions` - Deploy Azure Functions only

## 📚 Documentation

### [Implementation Plan](docs/planning/implementation-plan.md)

Comprehensive 2-week MVP development plan with task tracking and multi-agent coordination.

### [Multi-Agent Sync](docs/planning/multi-agent-sync.md)

Active agent coordination and task status tracking for parallel development.

### [Azure Deployment Guide](docs/deployment/azure-deployment-guide.md)

Infrastructure setup and deployment procedures for Azure resources.

## 🎯 Architecture

### Successfully Created Resource

- **Name**: `steves-mom`
- **Resource Group**: `rg-steves-mom`
- **Location**: `eastus`
- **SKU**: `S0` (Standard tier)
- **Status**: ✅ Active
- **Endpoint**: `https://eastus.api.cognitive.microsoft.com/`

### Get API Keys

```bash
az cognitiveservices account keys list \
  --name "steves-mom" \
  --resource-group "rg-steves-mom"
```

## 🔧 Common Issues Resolved

1. **Quota Error**: Resolved by using `eastus` region instead of resource group region
2. **SKU Availability**: S0 tier successfully deployed despite initial errors
3. **Feature Access**: Full AIServices functionality available

## 📖 What's Included

- Complete troubleshooting process documentation
- Step-by-step solution guide
- Alternative solutions for different scenarios
- Best practices for Azure Cognitive Services
- Quick reference commands
- Troubleshooting checklist

## 🚀 Next Steps

1. Retrieve API keys using the command above
2. Test the service with your applications
3. Configure proper security and access controls
4. Set up monitoring and cost management

---

**Created**: August 6, 2025  
**Author**: Stephen Boyett  
**Purpose**: Document Azure Cognitive Services setup and troubleshooting

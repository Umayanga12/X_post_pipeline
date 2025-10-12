# Crypto News Pipe - Deployment Guide

This guide provides comprehensive instructions for deploying the Crypto News Pipe application to various environments and cloud platforms.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
- [Security Considerations](#security-considerations)

## Prerequisites

### Required Software

- Docker (version 20.10 or later)
- Docker Compose (version 2.0 or later)
- Git

### Optional (for cloud deployments)

- AWS CLI (for AWS deployment)
- Google Cloud CLI (for GCP deployment)
- DigitalOcean CLI (for DigitalOcean deployment)

### API Keys Required

- Twitter/X API credentials:
  - API Key
  - API Secret
  - Access Token
  - Access Token Secret

## Environment Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd crypto-news-pipe
```

### 2. Create Environment File

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:

```env
# Twitter/X API Credentials
X_API_KEY=your_actual_api_key
X_API_SECRET=your_actual_api_secret
X_ACCESS_TOKEN=your_actual_access_token
X_ACCESS_SECRET=your_actual_access_secret

# Ollama Configuration
OLLAMA_MODEL=hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF

# Application Settings
LOG_LEVEL=INFO
POSTED_FILE=posted.json
IMAGE_FOLDER=image
```

### 3. Prepare Image Directory

Ensure you have the image directory with appropriate subdirectories:

```bash
mkdir -p image/{crypto,nft,blockchain}
# Add your images to these directories
```

## Local Development

### Quick Start

Use the deployment script for easy setup:

```bash
# Make the deployment script executable
chmod +x deploy.sh

# Deploy for development
./deploy.sh dev
```

### Manual Setup

If you prefer manual setup:

```bash
# Build and start services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Development Features

- Hot reloading with volume mounts
- Detailed logging
- Easy debugging access

## Production Deployment

### Local Production Setup

```bash
# Deploy production environment locally
./deploy.sh prod
```

This uses the optimized production configuration with:
- Multi-stage Docker builds for smaller images
- Health checks for all services
- Resource limits and logging configuration
- Non-root user execution for security

### Production Features

- **Multi-stage builds**: Reduced image size
- **Health checks**: Automatic service monitoring
- **Resource limits**: Prevents resource exhaustion
- **Logging**: Structured JSON logs with rotation
- **Security**: Non-root user, minimal attack surface

## Cloud Deployment

### AWS ECS Deployment

#### Prerequisites

1. Install AWS CLI and configure credentials
2. Set environment variables:

```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=your_account_id
```

#### Deploy to AWS

```bash
./deploy.sh aws
```

This will:
- Create ECR repository
- Build and push Docker image
- Provide instructions for ECS deployment

#### Manual ECS Setup

1. Create ECS cluster
2. Create task definition using the pushed image
3. Configure environment variables in task definition
4. Create ECS service

### Google Cloud Run Deployment

#### Prerequisites

1. Install Google Cloud CLI
2. Set project ID:

```bash
export GCP_PROJECT_ID=your-project-id
export GCP_REGION=us-central1
```

#### Deploy to GCP

```bash
./deploy.sh gcp
```

This automatically:
- Builds and pushes image to Container Registry
- Deploys to Cloud Run
- Configures service settings

### DigitalOcean App Platform

#### Deploy to DigitalOcean

```bash
./deploy.sh digitalocean
```

This creates an `app.yaml` specification file. Then:

1. Push your code to GitHub
2. Create new app in DigitalOcean App Platform
3. Connect your GitHub repository
4. Use the generated `app.yaml` specification
5. Configure environment variables in the DigitalOcean dashboard

### Other Cloud Platforms

#### Azure Container Instances

```bash
# Build image
docker build -t crypto-news-pipe -f Dockerfile.prod .

# Tag for Azure Container Registry
docker tag crypto-news-pipe your-registry.azurecr.io/crypto-news-pipe

# Push to ACR
docker push your-registry.azurecr.io/crypto-news-pipe

# Deploy to ACI
az container create \
  --resource-group your-rg \
  --name crypto-news-pipe \
  --image your-registry.azurecr.io/crypto-news-pipe \
  --environment-variables X_API_KEY=xxx X_API_SECRET=xxx \
  --memory 2 \
  --cpu 1
```

## Monitoring and Troubleshooting

### Health Checks

All services include health checks:

- **Application**: Python import test
- **Ollama**: API endpoint test

### Viewing Logs

```bash
# Development logs
./deploy.sh logs

# Production logs  
./deploy.sh logs docker-compose.prod.yaml

# Specific service logs
docker-compose logs -f crypto-news-pipe
```

### Common Issues

#### 1. Ollama Service Not Ready

**Symptoms**: Application fails to connect to Ollama

**Solutions**:
- Increase startup timeout
- Check Ollama model download progress
- Verify network connectivity

```bash
# Check Ollama status
docker-compose exec ollama ollama list
```

#### 2. Memory Issues

**Symptoms**: OOMKilled containers

**Solutions**:
- Increase memory limits in compose file
- Use smaller Ollama models
- Optimize Python memory usage

#### 3. API Rate Limiting

**Symptoms**: 429 errors in logs

**Solutions**:
- Increase delays between posts
- Reduce posting frequency
- Check Twitter API limits

### Performance Optimization

#### Resource Tuning

Adjust resources based on your needs:

```yaml
# In docker-compose.prod.yaml
deploy:
  resources:
    limits:
      memory: 4G    # Increase for larger models
      cpus: '2.0'   # Increase for faster processing
```

#### Model Selection

Choose appropriate Ollama models:

- **Small models**: `hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF` (1GB RAM)
- **Medium models**: `hf.co/bartowski/Llama-3.2-3B-Instruct-GGUF` (2GB RAM)
- **Large models**: `llama3.1:8b` (8GB RAM)

## Security Considerations

### Environment Variables

- Never commit `.env` files to version control
- Use secrets management in production
- Rotate API keys regularly

### Container Security

- Application runs as non-root user
- Minimal base images used
- Regular security updates

### Network Security

- Use private networks in production
- Implement firewall rules
- Enable HTTPS where applicable

### Cloud Security

#### AWS
- Use IAM roles instead of access keys
- Enable CloudTrail logging
- Use VPC for network isolation

#### GCP
- Use service accounts
- Enable audit logging
- Implement IAM best practices

#### DigitalOcean
- Use App Platform environment variables
- Enable monitoring and alerts

## Backup and Recovery

### Data Backup

Important files to backup:
- `posted.json`: Tracks posted articles
- `image/`: Custom images
- `.env`: Configuration (securely)

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/backup_$DATE"

mkdir -p $BACKUP_DIR
cp posted.json $BACKUP_DIR/
cp -r image/ $BACKUP_DIR/
# Don't backup .env directly - use encrypted storage
```

### Recovery Process

1. Restore backed up files
2. Update environment variables
3. Restart services
4. Verify functionality

## Scaling Considerations

### Horizontal Scaling

- Multiple application instances
- Load balancer configuration
- Shared storage for posted.json
- Database for state management

### Vertical Scaling

- Increase CPU/memory limits
- Use larger Ollama models
- Optimize batch processing

## Cost Optimization

### Cloud Cost Tips

1. **Use spot instances** (AWS/GCP)
2. **Set resource limits** appropriately
3. **Use smaller models** if acceptable
4. **Implement auto-scaling**
5. **Monitor usage** regularly

### Resource Efficiency

- Use multi-stage builds
- Optimize image sizes
- Cache dependencies
- Minimize data transfer

## Maintenance

### Regular Tasks

1. **Update dependencies** monthly
2. **Rotate API keys** quarterly
3. **Clean up old data** weekly
4. **Monitor performance** continuously
5. **Update base images** for security patches

### Update Process

```bash
# Pull latest changes
git pull origin main

# Rebuild and redeploy
./deploy.sh prod

# Verify deployment
./deploy.sh status
```

## Support

For issues and questions:

1. Check logs first: `./deploy.sh logs`
2. Verify configuration: `./deploy.sh status`
3. Review this deployment guide
4. Check the main README.md for application-specific details

## Contributing

When contributing deployment improvements:

1. Test locally first
2. Update documentation
3. Consider all deployment targets
4. Maintain backward compatibility
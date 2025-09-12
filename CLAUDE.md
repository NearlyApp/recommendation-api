# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

### Core Development
- `bun run build` - Build the CDK TypeScript code
- `bun run synth` - Build and synthesize CDK stacks  
- `bun run deploy` - Build and deploy infrastructure to AWS

## Architecture Overview

This is a serverless recommendation API built on AWS using CDK for infrastructure and a hybrid TypeScript/Python stack.

### High-Level Architecture
The system follows an event-driven architecture with three main processing stages:
1. **Ingestion** (`/ingest`) - Validates and queues incoming data
2. **Processing** (SQS-triggered) - Generates embeddings and stores in OpenSearch
3. **Data Management** (`/data/{id}`) - Retrieves and manages processed data

### Infrastructure Components

**CDK Stack** (`cdk/`):
- Main app: `app.ts` creates stacks for multiple environments
- Stack: `RecommendationAPI.ts` orchestrates all AWS resources
- Constructs:
  - `Endpoints.ts` - API Gateway with Lambda integrations and Docker-based functions
  - `DataTable.ts` - DynamoDB table for tracking processing status
  - `ProcessingQueue.ts` - SQS queue with dead letter queue for failed processing

**API Components** (`api/`):
- `handlers.py` - Lambda entry points routing to specific handlers
- `lambdas/ingest.py` - Validates requests, queues messages, updates DDB status
- `worker/main.py` - SQS processor that generates embeddings and saves to OpenSearch
- `lambdas/data.py` - Manages data retrieval and deletion

### Data Flow
1. POST `/ingest` → Validate → Store status in DynamoDB → Send to SQS
2. SQS message → Worker processes → Generate embeddings → Store in OpenSearch → Update DynamoDB status
3. GET/DELETE `/data/{id}` → Retrieve/manage data from DynamoDB

### Technology Stack
- **Infrastructure**: AWS CDK (TypeScript), API Gateway, Lambda, SQS, DynamoDB
- **Backend**: Python with Pydantic for validation
- **Embeddings**: OpenAI via langchain-openai
- **Search**: OpenSearch for vector storage

### Key Dependencies
- **CDK**: Uses Docker images for Lambda functions via `Dockerfile.lambda`
- **Python**: Managed via `uv` with `pyproject.toml` and compiled `requirements.txt`
- **Environment**: Requires SSM parameters for OpenAI API key and OpenSearch configuration

### Configuration
- Environment configs in `cdk/config.ts`
- TSConfig optimized for CDK development with strict settings
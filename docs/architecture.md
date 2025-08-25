# Technical Architecture

## System Overview

The R2R Financial Close system is built on a **deterministic-first architecture** with transparent AI assistance. The core design principle is that all financial calculations are computed algorithmically, while AI provides explanations, suggestions, and narratives.

## Core Components

### 1. **LangGraph Workflow Engine**
- **Orchestration**: 21 sequential nodes covering the complete financial close process
- **State Management**: Immutable `R2RState` with datasets, exceptions, and evidence
- **Audit Trail**: Append-only logging with timestamps and lineage

### 2. **Deterministic Engines**
- **FX Translation**: Currency conversion with configurable policies
- **Reconciliation Engines**: Bank, AP/AR, Intercompany with rule-based matching
- **TB Integrity**: Trial balance validation and consolidation
- **Accruals**: Period-end adjustments and reversals
- **Flux Analysis**: Variance analysis vs budget/prior periods

### 3. **AI Services**
- **Narrative Generation**: Explanations for variances and exceptions
- **Fuzzy Matching**: Suggestions for reconciliation items
- **Risk Assessment**: Materiality and exception analysis
- **Root Cause Analysis**: Validation error explanations

### 4. **Provenance System**
- **Evidence References**: Links to source data and computations
- **Deterministic Runs**: Function calls with input/output hashes
- **Prompt Runs**: AI calls with prompts, responses, and metrics
- **Lineage Links**: Connections between inputs and outputs

## Data Flow

```
Input Data → Validation → FX Translation → Reconciliations → 
Accruals → Flux Analysis → JE Lifecycle → Gatekeeping → Reporting
```

## Key Design Principles

### **Deterministic First**
- All financial numbers computed algorithmically
- Reproducible results with immutable run IDs
- No hard-coded strings or manual adjustments

### **AI Transparency**
- Clear labeling: [DET]/[AI]/[HYBRID]
- AI never sets financial balances
- Configurable AI modes (off/assist/strict)

### **Audit Compliance**
- Complete evidence trails
- Immutable audit logs
- SOX control mapping
- Four-eyes approval workflows

### **Enterprise Scale**
- Multi-entity support (USD/EUR/GBP)
- Materiality-based processing
- SLA enforcement
- Performance monitoring

## Technology Stack

- **Framework**: Python + LangGraph
- **Data Processing**: Pandas
- **AI Integration**: OpenAI API
- **Validation**: Pydantic
- **CLI**: Rich console
- **Testing**: pytest with layered strategy

## Configuration

The system supports multiple configuration modes:
- **AI Mode**: off/assist/strict
- **Data Sources**: Configurable input paths
- **Output Formats**: JSON, CSV, evidence packs
- **Governance**: Materiality thresholds, approval workflows

## Performance Characteristics

- **Unit Tests**: <100ms per test
- **Integration Tests**: <5s per test  
- **E2E Tests**: <30s per test
- **Full Close**: <2 minutes for standard datasets
- **AI Latency**: <5s per AI call (cached)

## Security & Governance

- **Code Hashing**: Immutable code snapshots
- **Config Hashing**: Reproducible configurations
- **AI Cost Controls**: Token usage monitoring
- **Access Controls**: Four-eyes approval workflows
- **Audit Logging**: Complete operation trails

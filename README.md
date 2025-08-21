# R2R Financial Close Automation

An AI-powered financial close orchestration system built with LangGraph, demonstrating automated reconciliations, variance analysis, and forensic accounting capabilities for enterprise month-end close processes.

## Quick Start

1. **Setup Environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure API Keys**

   ```bash
   cp .env.example .env
   # Edit .env and add your Azure OpenAI or OpenAI API credentials
   ```

3. **Run Demo**

   ```bash
   python scripts/run_close.py
   ```

## Demo Forensic Scenarios

The system uses a **static dataset** representing TechCorp Holdings (3 entities) with embedded forensic scenarios that demonstrate real-world financial close challenges:

### 🕒 **Timing Differences ($45K)**

- **Issue**: Google payment received Aug 31, recorded Sep 1
- **Detection**: AR aging vs bank statement mismatch  
- **Auto-Solution**: Cut-off adjustment entry

### 🔄 **Duplicate Transactions ($12.5K)**

- **Issue**: Salesforce invoice paid twice with different payment references
- **Detection**: Duplicate entries in AP detail and bank statements
- **Auto-Solution**: Reverse duplicate payment

### 💱 **FX Revaluation (€850K)**

- **Issue**: EUR/USD rate changed from 1.085 to 1.092 affecting intercompany balance
- **Detection**: Currency rate variance analysis
- **Auto-Solution**: FX gain/loss journal entry

### 📊 **Accrual Reversal ($28K)**

- **Issue**: July payroll accrual not automatically reversed in August
- **Detection**: Accrual tracking vs GL balance comparison
- **Auto-Solution**: Manual reversal entry

### 🏢 **Intercompany Mismatches ($15K)**

- **Issue**: 1-2 day booking delays between entities
- **Detection**: Transaction date analysis across entities
- **Auto-Solution**: Align booking dates

## Advanced Usage

```bash
.venv/bin/python scripts/run_close.py --period 2025-08 --prior 2025-07 --entities 3 --seed 42
```

Optional flags:
- `--period` default: 2025-08
- `--prior` default: 2025-07  
- `--entities` default: 3 (uses static dataset)
- `--seed` default: 42

## Environment Configuration

The system loads configuration from a `.env` file in the repository root. Supported API providers:

**Azure OpenAI (Recommended):**

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=2024-06-01
AZURE_OPENAI_CHAT_DEPLOYMENT=your_chat_model
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=your_embeddings_model
R2R_ALLOW_NETWORK=1
```

**OpenAI (Alternative):**

```env
OPENAI_API_KEY=your_api_key_here
R2R_ALLOW_NETWORK=1
```

Without valid credentials or when `R2R_ALLOW_NETWORK` is not `1`, the system returns deterministic stub responses for offline testing.

## Tests

```bash
.venv/bin/python -m pytest -q
```

## System Architecture

The financial close pipeline is orchestrated using LangGraph with the following workflow:

1. **Orchestrate** → Plan and initialize tasks
2. **Ingest** → Load static forensic dataset
3. **Reconcile** → Account reconciliations (Cash, AR, AP) using policy thresholds
4. **Match** → AR-to-bank transaction matching
5. **Variance** → Flux analysis vs prior period with AI narratives
6. **Intercompany** → Cross-entity netting readiness
7. **Journals** → AI-assisted journal entry generation
8. **Gatekeeper** → HITL approvals with maker/checker workflow
9. **Compliance** → SOX attestation and controls
10. **Audit** → Finalize audit trail

**Key Features:**
- Static forensic dataset with embedded scenarios
- Multi-currency support (USD, EUR, GBP)
- Real-time AI analysis with offline fallbacks
- Complete audit trail and compliance reporting

## Notes

- venv-only workflow (no Conda required).
- Root `.env` is always discovered via `python-dotenv` and loaded automatically at runtime.

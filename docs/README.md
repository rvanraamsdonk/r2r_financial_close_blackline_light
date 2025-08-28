# R2R Financial Close (Light) — Documentation Index

This documentation describes a deterministic, policy-aligned financial close enhanced with visible AI assistance. All numbers are computed; AI assists with explanations, matching suggestions, and risk narratives. No hard-coded strings; all outputs are derived from the real data in `data/lite/`.

## Master Plan (single source of truth)
See `docs/briefs/master-plan-consolidated-2025-08-28.md`. All roadmap decisions, AI vs deterministic balance, forensic patterns (pattern-based v2), and UI priorities are maintained there.

## Quick Start

```bash
python3 -m venv .venv
. .venv/bin/activate
.venv/bin/pip install -r requirements.txt

# Run the close (defaults from .env)
.venv/bin/python scripts/run_close.py --period 2025-08

# Verify provenance (latest audit)
.venv/bin/python scripts/smoke_test.py
```

## Documentation Structure

### 📖 **User Guides** (`/user/`)
- **Getting Started**: `user/getting-started.md`
- **CLI Reference**: `user/cli-reference.md`
- **Demo Script**: `user/demo-script.md`
- **Runbook**: `user/runbook.md`

### 🏗️ **Architecture** (`/architecture/`)
- **System Overview**: `architecture/overview.md`
- **Technical Design**: `architecture/technical-design.md`
- **AI Strategy**: `architecture/ai-strategy.md`
- **Data Model**: `architecture/data-model.md`

### ⚙️ **Functional Modules** (`/modules/`)
- **Core Workflow**: `modules/workflow.md`
- **Individual Modules**: `modules/[module-name].md`
- **Process Documentation**: `modules/processes/`

### 🔧 **Development** (`/development/`)
- **Testing**: `development/testing.md`
- **API Reference**: `development/api-reference.md`
- **Contributing**: `development/contributing.md`

### 📊 **Reference** (`/reference/`)
- **Data Dictionary**: `reference/data-dictionary.md`
- **Configuration**: `reference/configuration.md`
- **Troubleshooting**: `reference/troubleshooting.md`

### 📋 **Evaluations** (`/evaluations/`)
- **Big 4 Assessment**: `evaluations/big4-assessment.md`
- **Test Architecture Review**: `evaluations/test-architecture-review.md`

## CLI Reference

### Core Flags
- `--period` YYYY-MM (required)
- `--prior` prior period YYYY-MM (optional)
- `--entity` entity code or ALL
- `--ai-mode` off | assist | strict
- `--data` input data path (default `data/lite`)
- `--out` output path (default `out`)
- `--show-prompts` include prompts in evidence pack
- `--save-evidence` export provenance JSON and artifacts

## Key Concepts

- **Deterministic Calculations**: All financial numbers computed algorithmically
- **AI Assistance**: Explanations, suggestions, and narratives (never sets balances)
- **Transparency**: All outputs labeled [DET]/[AI]/[HYBRID]
- **Provenance**: Complete audit trail with evidence links
- **Governance**: Configurable AI modes and approval workflows

See the repository root `README.md` for project-level details.

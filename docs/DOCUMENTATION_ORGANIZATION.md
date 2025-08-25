# Documentation Organization Guide

## Overview

This document describes the reorganized documentation structure for the R2R Financial Close system. The new organization follows a clear hierarchy based on user needs and content types.

## New Structure

```
docs/
├── README.md                           # Main documentation index
├── ARCHITECTURE.md                     # Technical architecture overview
├── DOCUMENTATION_ORGANIZATION.md       # This file
│
├── user/                               # 📖 User Guides
│   ├── getting-started.md             # Quick start guide
│   ├── cli-reference.md               # Command line interface reference
│   ├── demo-script.md                 # Demo script for presentations
│   ├── console_ui_v6.md               # Console UI documentation
│   ├── close_accountant_functional_journey.md
│   └── close_process_walkthrough.md
│
├── architecture/                       # 🏗️ Architecture
│   ├── overview.md                    # System architecture overview
│   ├── ai-strategy.md                 # AI integration strategy
│   ├── ai-transparency.md             # AI transparency framework
│   └── ai-infrastructure.md           # AI infrastructure details
│
├── modules/                           # ⚙️ Functional Modules
│   ├── functional_modules.md          # Core workflow overview
│   ├── period_init.md                 # Period initialization
│   ├── fx_translation.md              # Foreign exchange translation
│   ├── tb_diagnostics.md              # Trial balance diagnostics
│   ├── ap_ar_reconciliation.md        # AP/AR reconciliation
│   ├── bank_reconciliation.md         # Bank reconciliation
│   ├── intercompany_reconciliation.md # Intercompany reconciliation
│   ├── accruals.md                    # Accruals and provisions
│   ├── flux_analysis.md               # Variance analysis
│   ├── je_lifecycle.md                # Journal entry lifecycle
│   ├── gatekeeping.md                 # Gatekeeping and risk
│   ├── hitl.md                        # Human-in-the-loop
│   ├── close_reporting.md             # Close reporting
│   ├── metrics_and_controls.md        # Metrics and controls
│   ├── controls_mapping.md            # Controls mapping
│   ├── audit.md                       # Audit framework
│   └── processes/                     # Process-specific documentation
│
├── reference/                         # 📊 Reference
│   ├── data-dictionary.md             # Data dictionary
│   ├── provenance-schema.md           # Provenance schema
│   ├── email-evidence.md              # Email evidence system
│   └── subledger-loaders.md           # Subledger loading
│
├── development/                       # 🔧 Development
│   └── (development documentation)
│
└── evaluations/                       # 📋 Evaluations
    ├── big4-assessment.md             # Big 4 evaluation
    ├── test-architecture-review.md    # Test architecture review
    ├── test-implementation-status.md  # Test implementation status
    └── test-architecture-handover.md  # Test architecture handover
```

## Content Categories

### 📖 **User Guides** (`/user/`)
**Purpose**: Help users get started and use the system effectively
**Audience**: End users, accountants, auditors, stakeholders
**Content**: Getting started guides, CLI reference, demo scripts, UI documentation

### 🏗️ **Architecture** (`/architecture/`)
**Purpose**: Explain system design and technical decisions
**Audience**: Developers, architects, technical stakeholders
**Content**: System overview, AI strategy, technical design patterns

### ⚙️ **Functional Modules** (`/modules/`)
**Purpose**: Document individual system components and workflows
**Audience**: Developers, business analysts, process owners
**Content**: Module specifications, process flows, input/output definitions

### 📊 **Reference** (`/reference/`)
**Purpose**: Provide detailed technical reference information
**Audience**: Developers, system administrators, technical users
**Content**: Data schemas, configuration options, troubleshooting guides

### 🔧 **Development** (`/development/`)
**Purpose**: Support development and contribution activities
**Audience**: Developers, contributors
**Content**: API documentation, testing guides, contribution guidelines

### 📋 **Evaluations** (`/evaluations/`)
**Purpose**: External assessments and reviews
**Audience**: Stakeholders, auditors, evaluators
**Content**: Third-party assessments, architecture reviews, implementation status

## Migration Summary

### Files Moved
- `brief.md` → `user/getting-started.md`
- `runbook_cli.md` → `user/cli-reference.md`
- `demo_script.md` → `user/demo-script.md`
- `architecture.md` → `architecture/overview.md`
- `ai_strategy.md` → `architecture/ai-strategy.md`
- `ai_transparency.md` → `architecture/ai-transparency.md`
- `ai_infra.md` → `architecture/ai-infrastructure.md`
- `test_architecture.md` → `evaluations/test-architecture-review.md`
- `test_implementation_status.md` → `evaluations/test-implementation-status.md`
- `big4_evaluation.md` → `evaluations/big4-assessment.md`
- `data_dictionary.md` → `reference/data-dictionary.md`
- `provenance_schema.md` → `reference/provenance-schema.md`
- `email_evidence.md` → `reference/email-evidence.md`
- `subledger_loaders.md` → `reference/subledger-loaders.md`
- `ui/*` → `user/*`
- `process/*` → `architecture/*`

### Files Renamed
- All files converted to kebab-case naming convention
- Removed underscores in favor of hyphens for better readability

## Benefits of New Organization

### 1. **Clear User Journey**
- New users start with `/user/getting-started.md`
- Technical users can dive into `/architecture/`
- Developers find relevant info in `/modules/` and `/reference/`

### 2. **Logical Grouping**
- Related content is grouped together
- Easy to find specific types of documentation
- Clear separation of concerns

### 3. **Scalability**
- New documentation can be added to appropriate categories
- Subdirectories can be created as needed
- Structure supports growth

### 4. **Maintainability**
- Consistent naming conventions
- Clear ownership of different content types
- Easy to update and reorganize

## Navigation Guidelines

### For New Users
1. Start with `docs/README.md`
2. Read `user/getting-started.md`
3. Try `user/demo-script.md`
4. Reference `user/cli-reference.md` as needed

### For Developers
1. Review `architecture/overview.md`
2. Study `modules/functional_modules.md`
3. Dive into specific modules in `/modules/`
4. Reference technical details in `/reference/`

### For Evaluators
1. Review `evaluations/big4-assessment.md`
2. Check `evaluations/test-architecture-review.md`
3. Examine `architecture/` for technical depth

## Future Enhancements

### Planned Additions
- `/development/api-reference.md` - API documentation
- `/development/contributing.md` - Contribution guidelines
- `/reference/configuration.md` - Configuration reference
- `/reference/troubleshooting.md` - Troubleshooting guide

### Potential Improvements
- Add search functionality
- Create documentation templates
- Implement versioning for API docs
- Add interactive examples

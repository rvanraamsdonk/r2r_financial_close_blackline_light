# R2R Financial Close UI Design Requirements

## Core Principles
1. **Clear AI/DET Distinction**
   - Visual indicators for all AI-generated content
   - Confidence scoring (0-100%) displayed prominently
   - Deterministic calculations marked with [DET] badge

2. **Audit Compliance**
   - Immutable artifact IDs
   - Complete provenance tracking
   - Workpaper reference system

3. **Accountant Workflow**
   - Bulk action processing
   - Keyboard navigation
   - Risk-based prioritization

## Component Specifications

### 1. Workflow Navigator
```
[● Init] [● Period] [▶ Data] [○ FX] [○ TB]
```
- Phase completion indicators
- Real-time progress metrics
- Estimated time remaining

### 2. Evidence Explorer
```
[Source Panel] [Data Panel] [Analysis Panel]
```
- Three-panel unified design
- Context-preserving navigation
- Standardized evidence cards

### 3. Action Center
```
Priority | Exception | Amount | Status
-------------------------------------
🔴 High | Dup Payment | $12.5K | Pending
```
- Bulk approval/rejection
- Tick mark integration
- Workpaper reference fields

### 4. Forensic Dashboard
```
RISK HEATMAP         AI CONFIDENCE
[ENT101] ████████    ██████ 90-100%
```
- Materiality thresholds
- Exception categorization
- Visual risk indicators

## Technical Implementation

### Data Requirements
```json
{
  "source": "AI|DET",
  "confidence": 0.85,
  "artifact_id": "ACCR-202508-ENT101-004"
}
```

### API Endpoints
- `GET /workflow/status` - Phase progress
- `POST /evidence/search` - Unified explorer
- `PATCH /actions/bulk` - Mass approvals

### UI Framework
- FastAPI backend
- HTMX for dynamic updates
- Tailwind CSS styling

## Validation Criteria
1. All data points show AI/DET source
2. Full audit trail for all actions
3. <50ms response time for bulk actions
4. 100% keyboard navigation coverage

## Revision History
- 2025-09-02: Initial version

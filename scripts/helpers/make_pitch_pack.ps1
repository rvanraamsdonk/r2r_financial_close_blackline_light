# Requires: PowerShell 5+
# Optional: pandoc installed and available on PATH for PDF export

param(
    [string]$OutDir = "out/pitch_pack",
    [string]$OutMarkdown = "pitch_pack.md",
    [string]$OutPdf = "pitch_pack.pdf"
)

$ErrorActionPreference = "Stop"

# Resolve repo root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

# Paths
$OutDirFull = Join-Path $RepoRoot $OutDir
New-Item -ItemType Directory -Force -Path $OutDirFull | Out-Null

$DestMd = Join-Path $OutDirFull $OutMarkdown
$DestPdf = Join-Path $OutDirFull $OutPdf

# Source files (ordered)
$files = @(
    "docs/briefs/pitch_pack.md",
    "docs/briefs/kpi_dashboard.md",
    "docs/modules/functional_modules.md",
    "docs/modules/metrics_and_controls.md",
    "docs/modules/fx_translation.md",
    "docs/modules/bank_reconciliation.md",
    "docs/modules/ap_ar_reconciliation.md",
    "docs/modules/intercompany_reconciliation.md",
    "docs/modules/accruals.md",
    "docs/modules/je_lifecycle.md",
    "docs/modules/flux_analysis.md",
    "docs/modules/journal_entries.md",
    "docs/modules/gatekeeping.md",
    "docs/modules/controls_mapping.md",
    "docs/modules/close_reporting.md"
)

# Concatenate to a single markdown
"# Agentic Controllership Pitch Pack\n" | Set-Content -Path $DestMd -Encoding UTF8

foreach ($rel in $files) {
    $path = Join-Path $RepoRoot $rel
    if (-not (Test-Path $path)) {
        Write-Warning "Missing: $rel"
        continue
    }
    "\n---\n\n" | Add-Content -Path $DestMd -Encoding UTF8
    Get-Content $path -Raw | Add-Content -Path $DestMd -Encoding UTF8
}

Write-Host "Wrote: $DestMd"

# Try to export to PDF via pandoc if available
$pandoc = Get-Command pandoc -ErrorAction SilentlyContinue
if ($pandoc) {
    Write-Host "Pandoc found at $($pandoc.Source). Generating PDF..."
    & $pandoc.Source $DestMd -o $DestPdf --from gfm --pdf-engine=wkhtmltopdf 2>$null
    if (Test-Path $DestPdf) {
        Write-Host "Wrote: $DestPdf"
    } else {
        Write-Warning "Pandoc did not produce $DestPdf. Ensure a PDF engine (e.g., wkhtmltopdf) is installed."
    }
} else {
    Write-Warning "pandoc not found on PATH. Skipping PDF export. To install: https://pandoc.org/installing.html"
}

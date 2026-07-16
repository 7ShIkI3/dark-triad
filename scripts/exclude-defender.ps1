# 🜏 The Dark Triad — Windows Defender Exclusions
# À exécuter en ADMINISTRATEUR (clic droit > Run as Administrator)
# Sinon Defender va bouffer impacket, scapy, nuclei templates, etc.

$ErrorActionPreference = 'Stop'

$paths = @(
    'C:\Users\attometre\dark-triad'            # Projet principal
    'C:\Users\attometre\dark-triad\references'  # Decepticon + autres refs
    'C:\Users\attometre\dark-triad\src'         # Code source
    'C:\Users\attometre\dark-triad\tests'       # Tests (payloads)
    'C:\Users\attometre\dark-triad\sandbox_data' # Artefacts sandbox
)

$extensions = @(
    '.py', '.ps1', '.sh', '.exe', '.dll',
    '.whl', '.tar.gz', '.zip', '.yar', '.yara'
)

$processes = @(
    'python.exe', 'pythonw.exe', 'docker.exe',
    'msfconsole.exe', 'nmap.exe'
)

Write-Host "🜏 THE DARK TRIAD — Defender Exclusions" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor DarkRed
Write-Host ""

# Chemins
foreach ($path in $paths) {
    if (Test-Path $path) {
        Add-MpPreference -ExclusionPath $path -ErrorAction SilentlyContinue
        Write-Host "  ✅ Path: $path" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Not found (skipped): $path" -ForegroundColor Yellow
    }
}

# Extensions
foreach ($ext in $extensions) {
    Add-MpPreference -ExclusionExtension $ext -ErrorAction SilentlyContinue
    Write-Host "  ✅ Extension: $ext" -ForegroundColor Cyan
}

# Processus
foreach ($proc in $processes) {
    Add-MpPreference -ExclusionProcess $proc -ErrorAction SilentlyContinue
    Write-Host "  ✅ Process: $proc" -ForegroundColor Magenta
}

Write-Host ""
Write-Host "🜏 Done. Defender won't touch The Dark Triad." -ForegroundColor Red
Write-Host "   Verify: Get-MpPreference | Select-Object -ExpandProperty ExclusionPath" -ForegroundColor Gray

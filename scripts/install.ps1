# Kamil AI Gamer - one-line terminal installer (Windows PowerShell).
#
#   irm https://raw.githubusercontent.com/k58804494-pixel/ai-roblex-ai/main/scripts/install.ps1 | iex
#
# Env overrides (set before running):
#   $env:KAMIL_REF    = "main"   # git ref to install
#   $env:KAMIL_EXTRAS = "all"    # pip extras (all | vision | control | llm | config | detect)
$ErrorActionPreference = "Stop"

$Repo   = if ($env:KAMIL_REPO)   { $env:KAMIL_REPO }   else { "https://github.com/k58804494-pixel/ai-roblex-ai" }
$Ref    = if ($env:KAMIL_REF)    { $env:KAMIL_REF }    else { "main" }
$Extras = if ($env:KAMIL_EXTRAS) { $env:KAMIL_EXTRAS } else { "all" }
$Spec   = "kamil-ai-gamer[$Extras] @ git+$Repo@$Ref"

function Say($m) { Write-Host "[kamil] $m" -ForegroundColor Cyan }

# --- pick a python -----------------------------------------------------------
$Python = $null
foreach ($c in @("python", "python3", "py")) {
  if (Get-Command $c -ErrorAction SilentlyContinue) { $Python = $c; break }
}
if (-not $Python) {
  Write-Error "Python 3.10+ not found. Install it from https://www.python.org/downloads/ (check 'Add to PATH')."
  exit 1
}
Say "Using $(& $Python --version)"

# Git is required to fetch from GitHub.
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Error "git not found. Install Git for Windows: https://git-scm.com/download/win"
  exit 1
}

# --- install -----------------------------------------------------------------
if (Get-Command pipx -ErrorAction SilentlyContinue) {
  Say "Installing with pipx (isolated)..."
  pipx install --force $Spec
} else {
  $KamilHome = if ($env:KAMIL_HOME) { $env:KAMIL_HOME } else { Join-Path $env:USERPROFILE ".kamil-ai-gamer" }
  $Venv = Join-Path $KamilHome "venv"
  Say "pipx not found - installing into a managed venv at $Venv"
  & $Python -m venv $Venv
  & (Join-Path $Venv "Scripts\python.exe") -m pip install --upgrade pip | Out-Null
  & (Join-Path $Venv "Scripts\pip.exe") install $Spec
  $Exe = Join-Path $Venv "Scripts\kamil-gamer.exe"
  Say "Installed. Run it with:"
  Say "  $Exe --game roblox --cycles 3"
}

Say "Installed! For local AI vision/chat (no API key) install Ollama (https://ollama.com):"
Say "  ollama pull llava ; ollama pull llama3.2"

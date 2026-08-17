$ErrorActionPreference = "Stop"
$repo = "magonlia2333-afk/daily-ai-cards"

function Set-FromClipboard([string]$Name, [string]$Prompt) {
  Write-Host "$Prompt - copy it to the clipboard, then press Enter."
  Read-Host | Out-Null
  $value = Get-Clipboard -Raw
  if ([string]::IsNullOrWhiteSpace($value)) { throw "Clipboard is empty for $Name." }
  $value.Trim() | gh secret set $Name --repo $repo
}

Set-FromClipboard "OPENAI_BASE_URL" "OpenAI-compatible API base URL, usually ending in /v1"
Set-FromClipboard "OPENAI_MODEL" "Model name supported by your provider"
Set-FromClipboard "OPENAI_API_KEY" "API key"
Write-Host "Third-party OpenAI provider configured."

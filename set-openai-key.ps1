$ErrorActionPreference = "Stop"
$repo = "magonlia2333-afk/daily-ai-cards"
Write-Host "Copy the complete OpenAI API key to the clipboard, then press Enter."
Read-Host | Out-Null
$key = Get-Clipboard -Raw
if ([string]::IsNullOrWhiteSpace($key)) { throw "Clipboard is empty." }
$key.Trim() | gh secret set OPENAI_API_KEY --repo $repo
Write-Host "OPENAI_API_KEY updated."

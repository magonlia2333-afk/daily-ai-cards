param(
  [string]$Repo = "magonlia2333-afk/daily-ai-cards"
)

$ErrorActionPreference = "Stop"
gh auth status | Out-Host

function Set-ClipboardGhSecret([string]$Name, [string]$Prompt) {
  Write-Host "$Prompt - copy the value, then press Enter"
  Read-Host | Out-Null
  $value = Get-Clipboard -Raw
  if ([string]::IsNullOrWhiteSpace($value)) { throw "Clipboard is empty for $Name" }
  $value.Trim() | gh secret set $Name --repo $Repo
}

Set-ClipboardGhSecret "OPENAI_API_KEY" "OpenAI API key"
Set-ClipboardGhSecret "OPENAI_BASE_URL" "OpenAI-compatible API base URL, for example https://provider.example/v1"
Set-ClipboardGhSecret "OPENAI_MODEL" "Model name supported by your provider, for example gpt-4o-mini"
Set-ClipboardGhSecret "RESEND_API_KEY" "Resend API key"
Set-ClipboardGhSecret "MAIL_FROM" "Verified sender email"
Set-ClipboardGhSecret "MAIL_TO" "Recipient email"
Write-Host "Secrets configured for $Repo"

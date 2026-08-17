param(
  [string]$Repo = "magonlia2333-afk/daily-ai-cards"
)

$ErrorActionPreference = "Stop"
gh auth status | Out-Host

function Set-SecureGhSecret([string]$Name, [string]$Prompt) {
  $secure = Read-Host $Prompt -AsSecureString
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try {
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    $plain | gh secret set $Name --repo $Repo
  } finally {
    if ($ptr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
  }
}

Set-SecureGhSecret "OPENAI_API_KEY" "OpenAI API key"
Set-SecureGhSecret "RESEND_API_KEY" "Resend API key"
Set-SecureGhSecret "MAIL_FROM" "Verified sender email"
Set-SecureGhSecret "MAIL_TO" "Recipient email"
Write-Host "Secrets configured for $Repo"

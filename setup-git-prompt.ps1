# PowerShell Git Prompt Setup Script
# Remove-Item $PROFILE -Force
Write-Host "Setting up Git branch display in PowerShell..." -ForegroundColor Green

# Check if profile exists
if (!(Test-Path $PROFILE)) {
    Write-Host "Creating PowerShell profile..." -ForegroundColor Yellow
    New-Item -Path $PROFILE -Type File -Force | Out-Null
}

# Profile content
$profileContent = @'
# Git Branch Display Function
function Get-GitBranch {
    try {
        $branch = git rev-parse --abbrev-ref HEAD 2>$null
        if ($branch) {
            return " [$branch]"
        }
    }
    catch {
        return ""
    }
    return ""
}

# Custom prompt with Git branch
function prompt {
    $gitBranch = Get-GitBranch
    
    Write-Host "PS " -NoNewline -ForegroundColor White
    Write-Host (Get-Location) -ForegroundColor Cyan -NoNewline
    if ($gitBranch) {
        Write-Host $gitBranch -ForegroundColor Yellow -NoNewline
    }
    Write-Host ""
    # return "PS " + (Get-Location) + $gitBranch + "> "
    return "PS > "
}

Write-Host "Git prompt loaded! Current location shows Git branch if available." -ForegroundColor Green
'@

# Replace profile content instead of adding to it
Set-Content -Path $PROFILE -Value $profileContent -Encoding UTF8

Write-Host "✅ Git prompt setup complete!" -ForegroundColor Green
Write-Host "Restart PowerShell or run: . `$PROFILE" -ForegroundColor Yellow
Write-Host "Your prompt will now show: PS C:\path\to\repo [branch-name]" -ForegroundColor Cyan

Param(
    [string]$ProjectRoot = "",
    [string]$EnvFile = ".env",
    [string]$KeyName = "ANTHROPIC_API_KEY",
    [string]$StartupCommand = "",
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"

function Resolve-ProjectRoot {
    Param([string]$InputPath)

    if ([string]::IsNullOrWhiteSpace($InputPath)) {
        if ($PSScriptRoot) {
            return (Resolve-Path (Join-Path $PSScriptRoot ".."))
        }
        return (Get-Location)
    }

    return (Resolve-Path $InputPath)
}

function Get-EnvValueFromFile {
    Param(
        [string]$FilePath,
        [string]$Name
    )

    if (-not (Test-Path $FilePath)) {
        throw "Env file not found: $FilePath"
    }

    $line = Get-Content $FilePath |
        Where-Object { $_ -match "^\s*$Name\s*=" } |
        Select-Object -First 1

    if (-not $line) {
        throw "Key '$Name' not found in $FilePath"
    }

    $parts = $line -split "=", 2
    if ($parts.Count -lt 2) {
        throw "Invalid env line format for '$Name'"
    }

    $value = $parts[1].Trim()
    if ($value.StartsWith('"') -and $value.EndsWith('"')) {
        $value = $value.Substring(1, $value.Length - 2)
    }
    if ($value.StartsWith("'") -and $value.EndsWith("'")) {
        $value = $value.Substring(1, $value.Length - 2)
    }

    if ([string]::IsNullOrWhiteSpace($value)) {
        throw "Key '$Name' has an empty value in $FilePath"
    }

    return $value
}

function Resolve-EnvFilePath {
    Param(
        [string]$Root,
        [string]$RequestedEnvFile
    )

    $requestedPath = Join-Path $Root $RequestedEnvFile
    if (Test-Path $requestedPath) {
        return $requestedPath
    }

    if ($RequestedEnvFile -eq ".env") {
        $fallbacks = @(".env.local", ".env.dev", ".env.txt")
        foreach ($candidate in $fallbacks) {
            $candidatePath = Join-Path $Root $candidate
            if (Test-Path $candidatePath) {
                return $candidatePath
            }
        }
    }

    throw "Env file not found. Checked: $requestedPath"
}

function Resolve-StartupCommand {
    Param(
        [string]$Root,
        [string]$ExplicitStartupCommand,
        [string]$ExplicitPythonExe
    )

    if (-not [string]::IsNullOrWhiteSpace($ExplicitStartupCommand)) {
        return $ExplicitStartupCommand
    }

    if (-not [string]::IsNullOrWhiteSpace($ExplicitPythonExe)) {
        return "& '$ExplicitPythonExe' main.py"
    }

    $marigoldPath = Join-Path $env:USERPROFILE "AppData/Local/anaconda3/envs/Marigold/python.exe"
    if (Test-Path $marigoldPath) {
        return "& '$marigoldPath' main.py"
    }

    return "python main.py"
}

$root = Resolve-ProjectRoot -InputPath $ProjectRoot
$envPath = Resolve-EnvFilePath -Root $root -RequestedEnvFile $EnvFile
$resolvedStartupCommand = Resolve-StartupCommand -Root $root -ExplicitStartupCommand $StartupCommand -ExplicitPythonExe $PythonExe
$keyValue = Get-EnvValueFromFile -FilePath $envPath -Name $KeyName

Write-Host "Project root: $root"
Write-Host "Loading key '$KeyName' from $envPath"

$oldValue = [Environment]::GetEnvironmentVariable($KeyName, "Process")
[Environment]::SetEnvironmentVariable($KeyName, $keyValue, "Process")

$sessionHeader = @"
Project Session Started
- Key name: $KeyName
- Scoped to this terminal process only
- Closing this terminal removes key automatically

Startup command:
$resolvedStartupCommand
"@

Write-Host $sessionHeader

try {
    Push-Location $root
    Invoke-Expression $resolvedStartupCommand

    Write-Host ""
    Write-Host "Interactive project shell is now active with $KeyName loaded."
    Write-Host "Type 'exit' to end session and remove key from this process."

    while ($true) {
        $cmd = Read-Host "project-shell>"
        if ($cmd -eq $null) { continue }
        if ($cmd.Trim().ToLower() -eq "exit") { break }
        if ([string]::IsNullOrWhiteSpace($cmd)) { continue }
        Invoke-Expression $cmd
    }
}
finally {
    Pop-Location
    if ($null -eq $oldValue) {
        Remove-Item "Env:$KeyName" -ErrorAction SilentlyContinue
    }
    else {
        [Environment]::SetEnvironmentVariable($KeyName, $oldValue, "Process")
    }
    Write-Host "$KeyName removed from current project session."
}

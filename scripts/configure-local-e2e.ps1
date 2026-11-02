param(
    [string]$PostgresContainer = "lexilingo-postgres"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Get-ContainerEnvironment([string]$containerName) {
    $raw = docker inspect $containerName
    if ($LASTEXITCODE -ne 0) {
        throw "Cannot inspect the local PostgreSQL container."
    }
    $item = @($raw | ConvertFrom-Json)[0]
    $map = @{}
    foreach ($entry in @($item.Config.Env)) {
        $parts = $entry -split "=", 2
        if ($parts.Count -eq 2) {
            $map[$parts[0]] = $parts[1]
        }
    }
    return $map
}

function Get-EnvMap([string]$path) {
    $map = @{}
    if (-not (Test-Path -LiteralPath $path)) {
        return $map
    }
    foreach ($line in Get-Content -LiteralPath $path -Encoding utf8) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$') {
            $value = $matches[2].Trim()
            if (
                ($value.StartsWith('"') -and $value.EndsWith('"')) -or
                ($value.StartsWith("'") -and $value.EndsWith("'"))
            ) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            $map[$matches[1]] = $value
        }
    }
    return $map
}

function Set-EnvValues([string]$path, [hashtable]$values) {
    $fullPath = [System.IO.Path]::GetFullPath($path)
    if (-not $fullPath.StartsWith($repoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to write outside the repository."
    }
    if (-not (Test-Path -LiteralPath $fullPath)) {
        throw "Required local env file is missing: $fullPath"
    }

    $remaining = @{}
    foreach ($key in $values.Keys) {
        $remaining[$key] = [string]$values[$key]
    }

    $lines = [System.Collections.Generic.List[string]]::new()
    foreach ($line in Get-Content -LiteralPath $fullPath -Encoding utf8) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=') {
            $key = $matches[1]
            if ($remaining.ContainsKey($key)) {
                $lines.Add("$key=$($remaining[$key])")
                $remaining.Remove($key)
                continue
            }
        }
        $lines.Add($line)
    }
    foreach ($key in ($remaining.Keys | Sort-Object)) {
        $lines.Add("$key=$($remaining[$key])")
    }

    $directory = Split-Path -Parent $fullPath
    $temporaryPath = Join-Path $directory (".{0}.{1}.tmp" -f ([System.IO.Path]::GetFileName($fullPath)), [System.IO.Path]::GetRandomFileName())
    try {
        [System.IO.File]::WriteAllLines($temporaryPath, $lines, $utf8NoBom)
        Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
    }
    finally {
        if (Test-Path -LiteralPath $temporaryPath) {
            Remove-Item -LiteralPath $temporaryPath -Force
        }
    }
}

function New-LocalSecret {
    $bytes = [byte[]]::new(48)
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($bytes)
    }
    finally {
        $generator.Dispose()
    }
    return ([BitConverter]::ToString($bytes) -replace "-", "").ToLowerInvariant()
}

function Keep-ValidGeminiKey([string]$value) {
    if ($value -match '^AIza[0-9A-Za-z_-]{20,}$') {
        return $value
    }
    return ""
}

function Keep-ValidGroqKey([string]$value) {
    if ($value -match '^gsk_[0-9A-Za-z_-]{20,}$') {
        return $value
    }
    return ""
}

$postgres = Get-ContainerEnvironment $PostgresContainer
foreach ($required in @("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB")) {
    if ([string]::IsNullOrWhiteSpace([string]$postgres[$required])) {
        throw "The running PostgreSQL container does not expose $required."
    }
}

$backendPath = Join-Path $repoRoot "backend-service\.env"
$aiPath = Join-Path $repoRoot "ai-service\.env"
$adminPath = Join-Path $repoRoot "admin-service\.env.local"
$flutterDevConfigPath = Join-Path $repoRoot "flutter-app\assets\env\dev_config"
$backendCurrent = Get-EnvMap $backendPath
$aiCurrent = Get-EnvMap $aiPath
$flutterDevConfig = Get-EnvMap $flutterDevConfigPath

$databaseUser = [Uri]::EscapeDataString([string]$postgres.POSTGRES_USER)
$databasePassword = [Uri]::EscapeDataString([string]$postgres.POSTGRES_PASSWORD)
$databaseName = [Uri]::EscapeDataString([string]$postgres.POSTGRES_DB)
$databaseUrl = "postgresql+asyncpg://${databaseUser}:${databasePassword}@127.0.0.1:5432/${databaseName}"

$jwtSecret = New-LocalSecret
$internalAiKey = New-LocalSecret
$cors = "http://127.0.0.1:5174,http://localhost:5174,http://127.0.0.1:5173,http://localhost:5173"
$backendGemini = Keep-ValidGeminiKey ([string]$backendCurrent.GEMINI_API_KEY)
$aiGemini = Keep-ValidGeminiKey ([string]$aiCurrent.GEMINI_API_KEY)
$aiGroq = Keep-ValidGroqKey ([string]$aiCurrent.GROQ_API_KEY)

Set-EnvValues $backendPath @{
    APP_ENV = "development"
    DEBUG = "True"
    DATABASE_URL = $databaseUrl
    REDIS_URL = "redis://127.0.0.1:6379/0"
    CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
    CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/0"
    AI_SERVICE_URL = "http://127.0.0.1:8001/api/v1"
    ALLOWED_ORIGINS = $cors
    # pydantic-settings JSON-decodes complex list fields before field validators.
    ALLOWED_HOSTS = '["localhost","127.0.0.1"]'
    ENABLE_APP_CORS = "True"
    SECRET_KEY = $jwtSecret
    AI_ADMIN_API_KEY = $internalAiKey
    GEMINI_API_KEY = $backendGemini
    FIREBASE_PROJECT_ID = "lexilingo-88492"
    GOOGLE_CLIENT_ID = [string]$flutterDevConfig.GOOGLE_SERVER_CLIENT_ID
    DEV_AUTO_VERIFY_EMAIL = "true"
    EMAIL_VERIFICATION_URL_BASE = "http://localhost:5174/#/verify-email"
    PORT = "8000"
}

Set-EnvValues $aiPath @{
    ENVIRONMENT = "development"
    DEBUG = "true"
    HOST = "127.0.0.1"
    PORT = "8001"
    BACKEND_SERVICE_URL = "http://127.0.0.1:8000"
    REDIS_URL = "redis://127.0.0.1:6379/1"
    MONGODB_URI = "mongodb://127.0.0.1:27017"
    MONGODB_DATABASE = "lexilingo"
    ALLOWED_ORIGINS = $cors
    SECRET_KEY = $jwtSecret
    AI_ADMIN_API_KEY = $internalAiKey
    GEMINI_API_KEY = $aiGemini
    GROQ_API_KEY = $aiGroq
}

Set-EnvValues $adminPath @{
    VITE_ENV = "development"
    VITE_BACKEND_URL = "http://127.0.0.1:8000/api/v1"
    VITE_AI_URL = "http://127.0.0.1:8001/api/v1"
    VITE_USE_GATEWAY = "false"
}

Write-Output "Local E2E env files configured without printing secrets."
Write-Output ("Gemini provider: backend={0}; ai={1}" -f ($(if ($backendGemini) { "configured" } else { "missing" })), $(if ($aiGemini) { "configured" } else { "missing" }))
Write-Output ("Groq provider: ai={0}" -f $(if ($aiGroq) { "configured" } else { "missing" }))

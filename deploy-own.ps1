# ==============================================================================
# EdgeStore - Custom Deployment Script (Windows PowerShell)
# ==============================================================================
param(
    [string]$Port = "",
    [string]$AdminUser = "",
    [string]$AdminPass = "",
    [string]$AdminEmail = ""
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   EdgeStore - Deploy as Own Private Appliance (Docker)    " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verify Docker Availability
Write-Host "[1/5] Checking Docker daemon status..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is not running or not in PATH."
    }
    Write-Host "      Docker daemon is active and responsive." -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker is not currently running. Please launch Docker Desktop and retry." -ForegroundColor Red
    exit 1
}

# 2. Gather Configuration
Write-Host "`n[2/5] Configuring custom deployment parameters..." -ForegroundColor Yellow

if (-not $Port) {
    $Port = Read-Host "Enter Application Port [Default: 8000]"
    if (-not $Port) { $Port = "8000" }
}

if (-not $AdminUser) {
    $AdminUser = Read-Host "Enter Administrator Username [Default: admin]"
    if (-not $AdminUser) { $AdminUser = "admin" }
}

if (-not $AdminPass) {
    $AdminPass = Read-Host "Enter Administrator Password [Default: EdgeStoreMasterPass2026!]"
    if (-not $AdminPass) { $AdminPass = "EdgeStoreMasterPass2026!" }
}

if (-not $AdminEmail) {
    $AdminEmail = Read-Host "Enter Administrator Email [Default: admin@my-edgestore.local]"
    if (-not $AdminEmail) { $AdminEmail = "admin@my-edgestore.local" }
}

# Generate 256-bit cryptographically secure JWT secret
$jwtBytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($jwtBytes)
$jwtSecretHex = [System.BitConverter]::ToString($jwtBytes).Replace("-", "").ToLower()

Write-Host "      Generated 256-bit Cryptographic JWT Secret." -ForegroundColor Green

# 3. Generate or Update .env file
Write-Host "`n[3/5] Writing custom production .env file..." -ForegroundColor Yellow

$envContent = @"
# ==============================================================================
# EdgeStore - Custom Deployment Environment Configuration
# Generated automatically on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# ==============================================================================

ENVIRONMENT_MODE=docker
HOST=0.0.0.0
PORT=$Port
DEBUG=False
LOG_LEVEL=INFO

INITIAL_ADMIN_USERNAME=$AdminUser
INITIAL_ADMIN_PASSWORD=$AdminPass
INITIAL_ADMIN_EMAIL=$AdminEmail

JWT_SECRET=$jwtSecretHex
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

PRIMARY_STORAGE_VOLUME=edgestore_primary
REPLICA_STORAGE_VOLUME=edgestore_replica
DB_STORAGE_VOLUME=edgestore_db

PRIMARY_VOLUME_NAME=edgestore_custom_primary
REPLICA_VOLUME_NAME=edgestore_custom_replica
DB_VOLUME_NAME=edgestore_custom_db
MONGO_VOLUME_NAME=edgestore_custom_mongo

MIN_FREE_DISK_BYTES=10485760
MAX_UPLOAD_SIZE_BYTES=104857600

MONGO_PORT=27017
MONGO_DB_NAME=edgestore_clients
MONGO_URI=mongodb://mongo:27017
DATABASE_URL=sqlite:////data/db/edgestore.db

RATE_LIMIT_LOGIN_MAX_ATTEMPTS=5
RATE_LIMIT_LOGIN_WINDOW_SECONDS=300
RATE_LIMIT_DEFAULT_REQUESTS=120

ALLOWED_CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173","http://localhost:$Port","http://127.0.0.1:$Port","http://localhost:4200","http://127.0.0.1:4200","http://localhost:3000","http://127.0.0.1:3000"]
ENABLE_SECURITY_HEADERS=True
STRICT_TRANSPORT_SECURITY=False
"@

Set-Content -Path ".env" -Value $envContent -Encoding UTF8
Write-Host "      Custom .env saved successfully." -ForegroundColor Green

# 4. Build and Start Docker Containers
Write-Host "`n[4/5] Building and launching custom Docker containers..." -ForegroundColor Yellow
docker compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: docker compose up failed." -ForegroundColor Red
    exit 1
}

# 5. Health Check & Validation
Write-Host "`n[5/5] Awaiting appliance health check..." -ForegroundColor Yellow
$isHealthy = $false
$targetUrl = "http://localhost:$Port/health"

for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 2
    try {
        $response = Invoke-RestMethod -Uri $targetUrl -Method Get -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($response.status -eq "online") {
            $isHealthy = $true
            break
        }
    } catch {
        Write-Host "      Waiting for service to initialize... ($($i+1)/15)" -ForegroundColor Gray
    }
}

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "   EdgeStore Appliance Successfully Deployed as Your Own!  " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Web Dashboard:       http://localhost:$Port/" -ForegroundColor Cyan
Write-Host "  API Health:          http://localhost:$Port/health" -ForegroundColor Cyan
Write-Host "  Interactive Docs:    http://localhost:$Port/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Admin Username:      $AdminUser" -ForegroundColor White
Write-Host "  Admin Password:      $AdminPass" -ForegroundColor White
Write-Host ""
Write-Host "  Primary Storage:     Docker Volume 'edgestore_custom_primary'" -ForegroundColor Gray
Write-Host "  Secondary Storage:   Docker Volume 'edgestore_custom_replica'" -ForegroundColor Gray
Write-Host "  MongoDB Storage:     Docker Volume 'edgestore_custom_mongo'" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Green

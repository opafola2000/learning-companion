# Setup RDS PostgreSQL + App Runner VPC connector for Hanz Learning Companion
# Region: us-east-1 | Account: 054041090939
# Run from PowerShell: .\scripts\setup-rds-postgres.ps1

$ErrorActionPreference = "Stop"
$Region = "us-east-1"
$VpcId = "vpc-0ca164c66ee9652c2"
$SubnetA = "subnet-0fd505c951f729310"  # us-east-1a
$SubnetB = "subnet-0cb59418247f86ee7"  # us-east-1b
$DbIdentifier = "hanz-learning-companion"
$DbName = "learning_companion"
$DbUser = "hanzadmin"
$EngineVersion = "16.14"
$ServiceArn = "arn:aws:apprunner:us-east-1:054041090939:service/hanz-learning-companion/6edc53bde2a040b4a19261f6f3272915"

function Get-OrCreateSecurityGroup {
    param([string]$Name, [string]$Description)
    try {
        $sg = aws ec2 create-security-group `
            --group-name $Name --description $Description --vpc-id $VpcId `
            --region $Region --query "GroupId" --output text 2>&1
        if ($sg -match "InvalidGroup.Duplicate") {
            $sg = aws ec2 describe-security-groups `
                --filters "Name=group-name,Values=$Name" --region $Region `
                --query "SecurityGroups[0].GroupId" --output text
        }
        return $sg.Trim()
    } catch {
        throw "Failed to create/get security group $Name : $_"
    }
}

Write-Host "=== Step 1: Security groups ===" -ForegroundColor Cyan
$AppRunnerSg = Get-OrCreateSecurityGroup "hanz-apprunner-connector-sg" "App Runner VPC connector for Hanz Learning Companion"
$RdsSg = Get-OrCreateSecurityGroup "hanz-rds-postgres-sg" "RDS PostgreSQL for Hanz Learning Companion"
Write-Host "App Runner SG: $AppRunnerSg"
Write-Host "RDS SG:        $RdsSg"

try {
    aws ec2 authorize-security-group-ingress `
        --group-id $RdsSg --protocol tcp --port 5432 --source-group $AppRunnerSg `
        --region $Region | Out-Null
    Write-Host "RDS ingress: port 5432 from App Runner connector SG"
} catch {
    Write-Host "RDS ingress rule may already exist (OK)"
}

Write-Host "`n=== Step 2: DB subnet group ===" -ForegroundColor Cyan
try {
    aws rds create-db-subnet-group `
        --db-subnet-group-name hanz-learning-companion-subnet-group `
        --db-subnet-group-description "Hanz Learning Companion RDS subnets" `
        --subnet-ids $SubnetA $SubnetB --region $Region | Out-Null
    Write-Host "Subnet group created"
} catch {
    Write-Host "Subnet group may already exist (OK)"
}

Write-Host "`n=== Step 3: Generate DB password ===" -ForegroundColor Cyan
$DbPassword = python -c "import secrets; print(secrets.token_urlsafe(24))"
$PasswordFile = Join-Path $PSScriptRoot "..\backend\.rds-password"
$DbPassword | Set-Content -Path $PasswordFile -NoNewline
Write-Host "Password saved to: backend\.rds-password (DO NOT COMMIT)"
Write-Host "SAVE THIS PASSWORD NOW: $DbPassword"

Write-Host "`n=== Step 4: Create RDS PostgreSQL instance ===" -ForegroundColor Cyan
$existing = aws rds describe-db-instances --db-instance-identifier $DbIdentifier --region $Region --query "DBInstances[0].DBInstanceStatus" --output text 2>$null
if ($existing -and $existing -ne "None") {
    Write-Host "RDS instance already exists, status: $existing"
} else {
    aws rds create-db-instance `
        --db-instance-identifier $DbIdentifier `
        --db-instance-class db.t4g.micro `
        --engine postgres `
        --engine-version $EngineVersion `
        --master-username $DbUser `
        --master-user-password $DbPassword `
        --allocated-storage 20 `
        --storage-type gp3 `
        --db-name $DbName `
        --vpc-security-group-ids $RdsSg `
        --db-subnet-group-name hanz-learning-companion-subnet-group `
        --no-publicly-accessible `
        --backup-retention-period 7 `
        --region $Region
    Write-Host "RDS create started (5-10 min to become Available)"
}

Write-Host "`n=== Step 5: Wait for RDS Available ===" -ForegroundColor Cyan
aws rds wait db-instance-available --db-instance-identifier $DbIdentifier --region $Region
$Endpoint = aws rds describe-db-instances --db-instance-identifier $DbIdentifier --region $Region --query "DBInstances[0].Endpoint.Address" --output text
Write-Host "RDS endpoint: $Endpoint"

Write-Host "`n=== Step 6: Create App Runner VPC connector ===" -ForegroundColor Cyan
$connectors = aws apprunner list-vpc-connectors --region $Region --query "VpcConnectors[?VpcConnectorName=='hanz-learning-companion-vpc'].VpcConnectorArn | [0]" --output text
if ($connectors -and $connectors -ne "None") {
    $VpcConnectorArn = $connectors.Trim()
    Write-Host "VPC connector exists: $VpcConnectorArn"
} else {
    $VpcConnectorArn = aws apprunner create-vpc-connector `
        --vpc-connector-name hanz-learning-companion-vpc `
        --subnets $SubnetA $SubnetB `
        --security-groups $AppRunnerSg `
        --region $Region --query "VpcConnector.VpcConnectorArn" --output text
    Write-Host "VPC connector created: $VpcConnectorArn"
}

Write-Host "`n=== Step 7: Build DATABASE_URL ===" -ForegroundColor Cyan
$EncodedPassword = [uri]::EscapeDataString($DbPassword)
$DatabaseUrl = "postgresql+psycopg://${DbUser}:${EncodedPassword}@${Endpoint}:5432/${DbName}"
Write-Host "DATABASE_URL (for App Runner env var):"
Write-Host $DatabaseUrl

Write-Host "`n=== Step 8: Update App Runner service ===" -ForegroundColor Cyan
Write-Host "Run this manually in AWS Console OR approve the App Runner update command:"
Write-Host "  Configuration -> Environment variables -> DATABASE_URL"
Write-Host "  Configuration -> Networking -> VPC connector -> hanz-learning-companion-vpc"
Write-Host "Then redeploy the Docker image (includes psycopg driver)."

# Save connection info for reference
$InfoFile = Join-Path $PSScriptRoot "..\backend\rds-connection-info.txt"
@"
RDS Endpoint: $Endpoint
Database: $DbName
Username: $DbUser
Password file: backend\.rds-password
VPC Connector ARN: $VpcConnectorArn
DATABASE_URL=$DatabaseUrl
"@ | Set-Content -Path $InfoFile
Write-Host "`nConnection info saved to: backend\rds-connection-info.txt"

[CmdletBinding()]
param(
    [string]$EnvFile = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path
$sanitizeSqlPath = Join-Path $scriptDir "sanitize_staging.sql"

if (-not (Test-Path -LiteralPath $sanitizeSqlPath)) {
    throw "Required sanitization script not found: $sanitizeSqlPath"
}

if ([string]::IsNullOrWhiteSpace($EnvFile)) {
    $EnvFile = Join-Path $repoRoot ".env.staging-clone"
}

function Resolve-MySqlTool {
    param([Parameter(Mandatory)][string]$ToolName)

    $cmd = Get-Command $ToolName -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    if ($ToolName.EndsWith(".exe") -and ($IsLinux -or $IsMacOS)) {
        $bareName = $ToolName.Substring(0, $ToolName.Length - 4)
        $cmd = Get-Command $bareName -ErrorAction SilentlyContinue
        if ($cmd) {
            return $cmd.Source
        }
    }

    $workbenchPath = Join-Path "C:\Program Files\MySQL\MySQL Workbench 8.0 CE" $ToolName
    if (Test-Path -LiteralPath $workbenchPath) {
        return $workbenchPath
    }

    throw "Could not find $ToolName on PATH or at '$workbenchPath'. Install MySQL Workbench 8.0 CE or add MySQL client tools to PATH."
}

function Read-StagingCloneConfig {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Config file not found: $Path. Copy .env.staging-clone.example to .env.staging-clone and fill in local values."
    }

    $values = @{}
    foreach ($rawLine in [System.IO.File]::ReadAllLines($Path, [System.Text.Encoding]::UTF8)) {
        $line = $rawLine.Trim()
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) {
            continue
        }
        if ($line.StartsWith("export ")) {
            $line = $line.Substring(7).TrimStart()
        }
        $eqIndex = $line.IndexOf("=")
        if ($eqIndex -lt 1) {
            throw "Malformed line in ${Path}: $rawLine"
        }

        $key = $line.Substring(0, $eqIndex).Trim()
        $val = $line.Substring($eqIndex + 1).Trim()
        if ($val.Length -ge 2) {
            if (($val.StartsWith('"') -and $val.EndsWith('"')) -or ($val.StartsWith("'") -and $val.EndsWith("'"))) {
                $val = $val.Substring(1, $val.Length - 2)
            }
        }
        $val = [System.Environment]::ExpandEnvironmentVariables($val)
        $values[$key] = $val
    }

    foreach ($requiredKey in @("DB_HOST", "DB_CA_CERT_PATH", "PPRX_DUMP_USER", "PPRX_STAGING_USER")) {
        if (-not $values.ContainsKey($requiredKey) -or [string]::IsNullOrWhiteSpace($values[$requiredKey])) {
            throw "Missing required key '$requiredKey' in $Path"
        }
    }

    $portText = if ($values.ContainsKey("DB_PORT") -and -not [string]::IsNullOrWhiteSpace($values["DB_PORT"])) {
        $values["DB_PORT"]
    } else {
        "25060"
    }
    $portNum = 0
    if (-not [int]::TryParse($portText, [ref]$portNum) -or $portNum -lt 1 -or $portNum -gt 65535) {
        throw "Invalid DB_PORT '$portText' in $Path"
    }

    $caCertPath = $values["DB_CA_CERT_PATH"]
    if (-not (Test-Path -LiteralPath $caCertPath)) {
        throw "CA certificate file not found at DB_CA_CERT_PATH: $caCertPath"
    }

    return @{
        DbHost = $values["DB_HOST"]
        DbPort = $portNum.ToString()
        CaCertPath = (Resolve-Path -LiteralPath $caCertPath).Path
        DumpUser = $values["PPRX_DUMP_USER"]
        StagingUser = $values["PPRX_STAGING_USER"]
    }
}

function ConvertFrom-SecureStringPlaintext {
    param([Parameter(Mandatory)][System.Security.SecureString]$Secure)

    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
    try {
        return [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    } finally {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

function Get-MySqlPassword {
    param(
        [Parameter(Mandatory)][string]$EnvVarName,
        [Parameter(Mandatory)][string]$PromptText
    )

    $fromEnv = [System.Environment]::GetEnvironmentVariable($EnvVarName)
    if (-not [string]::IsNullOrEmpty($fromEnv)) {
        return $fromEnv
    }

    $secure = Read-Host -Prompt $PromptText -AsSecureString
    return ConvertFrom-SecureStringPlaintext -Secure $secure
}

function Invoke-WithMySqlPwd {
    param(
        [Parameter(Mandatory)][AllowEmptyString()][string]$Password,
        [Parameter(Mandatory)][scriptblock]$Action
    )

    $previous = $env:MYSQL_PWD
    $env:MYSQL_PWD = $Password
    try {
        & $Action
    } finally {
        if ($null -eq $previous) {
            Remove-Item Env:MYSQL_PWD -ErrorAction SilentlyContinue
        } else {
            $env:MYSQL_PWD = $previous
        }
    }
}

function Format-ProcessArg {
    param([Parameter(Mandatory)][string]$Value)

    if ($Value -notmatch '[\s"]') {
        return $Value
    }
    $escaped = $Value -replace '(\\*)"', '$1$1\"'
    $escaped = $escaped -replace '(\\+)$', '$1$1'
    return '"' + $escaped + '"'
}

function Invoke-MySqlInputFile {
    param(
        [Parameter(Mandatory)][string]$MysqlExe,
        [Parameter(Mandatory)][string[]]$BaseArgs,
        [Parameter(Mandatory)][string]$Database,
        [Parameter(Mandatory)][string]$SqlFilePath
    )

    $allArgs = $BaseArgs + @($Database)
    $quotedArgs = ($allArgs | ForEach-Object { Format-ProcessArg -Value $_ })
    $proc = Start-Process -FilePath $MysqlExe -ArgumentList $quotedArgs -RedirectStandardInput $SqlFilePath -NoNewWindow -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        throw "mysql failed with exit code $($proc.ExitCode) while executing $SqlFilePath against $Database"
    }
}

$mysqldumpExe = Resolve-MySqlTool -ToolName "mysqldump.exe"
$mysqlExe = Resolve-MySqlTool -ToolName "mysql.exe"
$config = Read-StagingCloneConfig -Path $EnvFile

$tempRoot = if (-not [string]::IsNullOrWhiteSpace($env:TEMP)) {
    $env:TEMP
} else {
    [System.IO.Path]::GetTempPath()
}
$runId = [System.Guid]::NewGuid().ToString("N")
$dumpSqlPath = Join-Path $tempRoot "pprx_prod_dump_$runId.sql"
$pass2SqlPath = Join-Path $tempRoot "pprx_prod_dump_${runId}_chart_pairs.sql"

$commonDumpArgs = @(
    "--host=$($config.DbHost)",
    "--port=$($config.DbPort)",
    "--user=$($config.DumpUser)",
    "--ssl-mode=VERIFY_CA",
    "--ssl-ca=$($config.CaCertPath)",
    "--single-transaction",
    "--set-gtid-purged=OFF",
    "--no-tablespaces",
    "--default-character-set=utf8mb4",
    "--quick",
    "--compress"
)
$pass1Args = $commonDumpArgs + @("--ignore-table=ebdb.chart_pairs", "--result-file=$dumpSqlPath", "ebdb")
$pass2Args = $commonDumpArgs + @("--no-data", "--result-file=$pass2SqlPath", "ebdb", "chart_pairs")

$commonMysqlArgs = @(
    "--host=$($config.DbHost)",
    "--port=$($config.DbPort)",
    "--user=$($config.StagingUser)",
    "--ssl-mode=VERIFY_CA",
    "--ssl-ca=$($config.CaCertPath)",
    "--default-character-set=utf8mb4"
)

if ($DryRun) {
    Write-Host "[dry-run] mysqldump: $mysqldumpExe"
    Write-Host "[dry-run] mysql:     $mysqlExe"
    Write-Host "[dry-run] env file:  $EnvFile"
    Write-Host "[dry-run] temp dump: $dumpSqlPath"
    Write-Host "[dry-run] pass 1:    $mysqldumpExe $($pass1Args -join ' ')"
    Write-Host "[dry-run] pass 2:    $mysqldumpExe $($pass2Args -join ' ')"
    Write-Host "[dry-run] drop:      $mysqlExe $($commonMysqlArgs -join ' ') --batch --skip-column-names -e `"SELECT table_type, table_name FROM information_schema.tables WHERE table_schema = 'pprx_staging';`" pprx_staging"
    Write-Host "[dry-run] restore:   $mysqlExe $($commonMysqlArgs -join ' ') pprx_staging < $dumpSqlPath"
    Write-Host "[dry-run] sanitize:  $mysqlExe $($commonMysqlArgs -join ' ') pprx_staging < $sanitizeSqlPath"
    return
}

$dumpPassword = Get-MySqlPassword -EnvVarName "PPRX_DUMP_PASSWORD" -PromptText "Enter MySQL password for $($config.DumpUser) (ebdb read-only)"
$stagingPassword = Get-MySqlPassword -EnvVarName "PPRX_STAGING_PASSWORD" -PromptText "Enter MySQL password for $($config.StagingUser) (pprx_staging)"

try {
    Write-Host "Dumping ebdb (pass 1: all tables except chart_pairs)..."
    Invoke-WithMySqlPwd -Password $dumpPassword -Action {
        & $mysqldumpExe @pass1Args
        if ($LASTEXITCODE -ne 0) {
            throw "mysqldump pass 1 failed with exit code $LASTEXITCODE; aborting before modifying pprx_staging."
        }
        if (-not (Test-Path -LiteralPath $dumpSqlPath) -or (Get-Item -LiteralPath $dumpSqlPath).Length -le 0) {
            throw "mysqldump pass 1 produced no output; aborting before modifying pprx_staging."
        }

        Write-Host "Dumping ebdb (pass 2: chart_pairs schema only)..."
        & $mysqldumpExe @pass2Args
        if ($LASTEXITCODE -ne 0) {
            throw "mysqldump pass 2 failed with exit code $LASTEXITCODE; aborting before modifying pprx_staging."
        }
        if (-not (Test-Path -LiteralPath $pass2SqlPath) -or (Get-Item -LiteralPath $pass2SqlPath).Length -le 0) {
            throw "mysqldump pass 2 produced no output; aborting before modifying pprx_staging."
        }
    }

    $outStream = [System.IO.File]::Open($dumpSqlPath, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write)
    try {
        $inStream = [System.IO.File]::OpenRead($pass2SqlPath)
        try {
            $inStream.CopyTo($outStream)
        } finally {
            $inStream.Dispose()
        }
    } finally {
        $outStream.Dispose()
    }
    Remove-Item -LiteralPath $pass2SqlPath -Force -ErrorAction SilentlyContinue

    Invoke-WithMySqlPwd -Password $stagingPassword -Action {
        Write-Host "Inspecting existing objects in pprx_staging..."
        $listSql = "SELECT table_type, table_name FROM information_schema.tables WHERE table_schema = 'pprx_staging';"
        $tableRows = & $mysqlExe @commonMysqlArgs --batch --skip-column-names -e $listSql "pprx_staging"
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to list existing tables in pprx_staging (mysql exit code $LASTEXITCODE)."
        }

        $views = @()
        $tables = @()
        foreach ($row in $tableRows) {
            if ([string]::IsNullOrWhiteSpace($row)) {
                continue
            }
            $parts = $row -split "`t", 2
            if ($parts.Length -lt 2) {
                continue
            }
            $tableType = $parts[0].Trim()
            $tableName = $parts[1].Trim()
            $quotedName = '`' + ($tableName -replace '`', '``') + '`'
            if ($tableType -eq "VIEW") {
                $views += $quotedName
            } else {
                $tables += $quotedName
            }
        }

        if ($views.Count -gt 0 -or $tables.Count -gt 0) {
            Write-Host "Dropping $($tables.Count) table(s) and $($views.Count) view(s) in pprx_staging..."
            $dropStatements = @("SET FOREIGN_KEY_CHECKS = 0")
            if ($views.Count -gt 0) {
                $dropStatements += "DROP VIEW IF EXISTS $($views -join ', ')"
            }
            if ($tables.Count -gt 0) {
                $dropStatements += "DROP TABLE IF EXISTS $($tables -join ', ')"
            }
            $dropStatements += "SET FOREIGN_KEY_CHECKS = 1"
            $dropSql = ($dropStatements -join "; ") + ";"

            & $mysqlExe @commonMysqlArgs -e $dropSql "pprx_staging"
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to drop existing objects in pprx_staging (mysql exit code $LASTEXITCODE)."
            }
        } else {
            Write-Host "No existing tables in pprx_staging to drop."
        }

        Write-Host "Restoring prod dump into pprx_staging..."
        Invoke-MySqlInputFile -MysqlExe $mysqlExe -BaseArgs $commonMysqlArgs -Database "pprx_staging" -SqlFilePath $dumpSqlPath

        Write-Host "Running User sanitization (scripts/sanitize_staging.sql)..."
        Invoke-MySqlInputFile -MysqlExe $mysqlExe -BaseArgs $commonMysqlArgs -Database "pprx_staging" -SqlFilePath $sanitizeSqlPath
    }

    Write-Host "Prod-to-staging clone and sanitization completed successfully."
} finally {
    Remove-Item -LiteralPath $dumpSqlPath, $pass2SqlPath -Force -ErrorAction SilentlyContinue
}

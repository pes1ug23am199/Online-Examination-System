param(
  [string]$SqlFile = "miniproject.sql"
)

# Reads MySQL connection from environment
$host = $env:MYSQL_HOST; if (-not $host) { $host = "127.0.0.1" }
$port = $env:MYSQL_PORT; if (-not $port) { $port = "3306" }
$user = $env:MYSQL_USER; if (-not $user) { $user = "root" }
$db   = $env:MYSQL_DB;   if (-not $db)   { $db   = "online_exam_system" }
$pwd  = $env:MYSQL_PASSWORD

if (-not (Test-Path $SqlFile)) {
  Write-Error "SQL file not found: $SqlFile"; exit 1
}

# Use MYSQL_PWD to avoid interactive prompt and avoid echoing the password
if ($pwd) { $env:MYSQL_PWD = $pwd }

# Ensure DB exists and import schema/data
$mysqlBase = "mysql --host=$host --port=$port --user=$user"

# Create DB if needed
cmd /c "$mysqlBase -e \"CREATE DATABASE IF NOT EXISTS `$db;\""
if ($LASTEXITCODE -ne 0) { Write-Error "Failed to ensure database exists"; exit 1 }

# Import file
cmd /c "$mysqlBase `$db < `"$SqlFile`""
if ($LASTEXITCODE -ne 0) { Write-Error "Import failed"; exit 1 }

Write-Host "Imported $SqlFile into database '$db' on $host:$port as $user"

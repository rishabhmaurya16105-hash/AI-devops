[CmdletBinding()]
param(
    [switch]$DryRunOnly,
    [string]$Kubeconfig = (Join-Path $env:TEMP "devopsmart-kind.kubeconfig"),
    [string]$Context = "kind-devopsmart"
)

$ErrorActionPreference = "Stop"
$namespace = "devopsmart"
$secretName = "postgres-secret"
$temporaryPath = Join-Path $env:TEMP (
    "devopsmart-postgres-password-" + [guid]::NewGuid().ToString("N") + ".tmp"
)
$randomBytes = New-Object byte[] 48
$passwordBytes = $null
$randomGenerator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$fileStream = $null

try {
    $randomGenerator.GetBytes($randomBytes)
    $password = [Convert]::ToBase64String($randomBytes).
        TrimEnd("=").Replace("+", "-").Replace("/", "_")
    $passwordBytes = [System.Text.Encoding]::UTF8.GetBytes($password)

    $fileStream = [System.IO.File]::Open(
        $temporaryPath,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    $fileStream.Dispose()
    $fileStream = $null

    $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
    $fileAcl = Get-Acl -LiteralPath $temporaryPath
    $fileAcl.SetAccessRuleProtection($true, $false)
    $accessRule = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList @(
        $currentUser,
        [System.Security.AccessControl.FileSystemRights]::FullControl,
        [System.Security.AccessControl.AccessControlType]::Allow
    )
    $fileAcl.SetAccessRule($accessRule)
    Set-Acl -LiteralPath $temporaryPath -AclObject $fileAcl

    [System.IO.File]::WriteAllBytes($temporaryPath, $passwordBytes)

    $secretArgs = @(
        "--kubeconfig", $Kubeconfig,
        "--context", $Context,
        "create", "secret", "generic", $secretName,
        "--namespace", $namespace,
        "--from-file=POSTGRES_PASSWORD=$temporaryPath",
        "--dry-run=server",
        "-o", "name"
    )
    & kubectl @secretArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Server-side Secret dry-run failed with exit code $LASTEXITCODE."
    }

    if ($DryRunOnly) {
        Write-Output "Secret dry-run passed for $namespace/$secretName and key POSTGRES_PASSWORD; no Secret was created."
    } else {
        $secretArgs = @(
            "--kubeconfig", $Kubeconfig,
            "--context", $Context,
            "create", "secret", "generic", $secretName,
            "--namespace", $namespace,
            "--from-file=POSTGRES_PASSWORD=$temporaryPath"
        )
        & kubectl @secretArgs
        if ($LASTEXITCODE -ne 0) {
            throw "Secret creation failed with exit code $LASTEXITCODE."
        }
        Write-Output "Created Secret $namespace/$secretName with key POSTGRES_PASSWORD."
    }
} finally {
    if ($null -ne $fileStream) {
        $fileStream.Dispose()
    }
    if (Test-Path -LiteralPath $temporaryPath) {
        Remove-Item -LiteralPath $temporaryPath -Force -ErrorAction SilentlyContinue
    }
    if ($null -ne $randomBytes) {
        [Array]::Clear($randomBytes, 0, $randomBytes.Length)
    }
    if ($null -ne $passwordBytes) {
        [Array]::Clear($passwordBytes, 0, $passwordBytes.Length)
    }
    if ($null -ne $randomGenerator) {
        $randomGenerator.Dispose()
    }
    $password = $null
}

Param(
    [string]$Configuration = 'Release',
    [string]$Runtime = 'win-x64',
    [string]$Project = 'winapp.csproj',
    [switch]$SingleFile
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projPath = Join-Path $scriptDir $Project
$publishDir = Join-Path $scriptDir "publish\$Runtime\$Configuration"

Write-Host "Publishing $projPath to $publishDir ..."

# Build publish argument list
$publishArgs = @('publish', $projPath, '-c', $Configuration, '-r', $Runtime, '-o', $publishDir)

if ($SingleFile) {
    # produce a single-file, self-contained executable
    $publishArgs += @('--self-contained', 'true', '/p:PublishSingleFile=true', '/p:PublishTrimmed=false')
} else {
    # framework-dependent default
    $publishArgs += @('--self-contained', 'false')
}

$ps = Start-Process -FilePath dotnet -ArgumentList $publishArgs -NoNewWindow -Wait -PassThru
if ($ps.ExitCode -ne 0) {
    Write-Error "dotnet publish failed with exit code $($ps.ExitCode). Ensure .NET SDK is installed and on PATH."
    exit $ps.ExitCode
}

# Locate swedll (common filenames)
$dllCandidates = @('swedll.dll','swedll64.dll','swedll32.dll')
$dllSource = $null
foreach ($d in $dllCandidates) {
    $p = Join-Path $scriptDir $d
    if (Test-Path $p) { $dllSource = $p; break }
}

# Fallback to extracted sweph folder
if (-not $dllSource) {
    $fallback = Join-Path $scriptDir 'sweph\sweph\bin\swedll64.dll'
    if (Test-Path $fallback) { $dllSource = $fallback }
}

if ($dllSource) {
    Copy-Item -Path $dllSource -Destination $publishDir -Force
    Write-Host "Copied $dllSource to $publishDir"
} else {
    Write-Warning "No swedll found. Place swedll.dll next to this script or in sweph\sweph\bin and re-run the script."
}
# Create ZIP of publish output for easy distribution
$zipName = "winapp-$Runtime-$Configuration.zip"
$zipPath = Join-Path $scriptDir "publish\$Runtime\$Configuration\..\$zipName"
try {
    if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
    Compress-Archive -Path (Join-Path $publishDir '*') -DestinationPath $zipPath -Force
    Write-Host "Created ZIP package: $zipPath"
} catch {
    Write-Warning "Failed to create ZIP package: $($_.Exception.Message)"
}

Write-Host "Publish complete. Run the executable from: $publishDir"
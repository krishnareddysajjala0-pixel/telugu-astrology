# compare_with_flask.ps1
# Runs the produced winapp exe with sample inputs and posts same inputs to the Flask app
# Requires:
# - The published single-file exe present at ./publish/win-x64/Release/<your-exe>.exe
# - The Flask app running locally at http://localhost:10000
# Usage: .\compare_with_flask.ps1

$exePath = Join-Path $PSScriptRoot 'publish\win-x64\Release\winapp.exe'
$flaskUrl = 'http://localhost:10000/chart'
$outDir = Join-Path $PSScriptRoot 'compare_output'
New-Item -Path $outDir -ItemType Directory -Force | Out-Null

$samples = @(
    @{ name='Test User'; dob='1990-05-15'; tob='08:30'; place='Hyderabad'; lat='17.3850'; lon='78.4867' },
    @{ name='Example'; dob='1985-12-01'; tob='23:15'; place='Mumbai'; lat='19.0760'; lon='72.8777' }
)

foreach ($s in $samples) {
    $id = ($s.dob -replace '-','') + '_' + ($s.tob -replace ':','')
    $exeOut = Join-Path $outDir "exe_$id.txt"
    $flaskOut = Join-Path $outDir "flask_$id.html"

    Write-Host "Running exe for $($s.name) -> $exeOut"
    $inputData = "$($s.name)`n$($s.dob)`n$($s.tob)`n$($s.lat)`n$($s.lon)`n"
    if (-Not (Test-Path $exePath)) { Write-Warning "Exe not found: $exePath. Build/publish first."; break }

    # Run the exe and capture stdout
    $pinfo = New-Object System.Diagnostics.ProcessStartInfo
    $pinfo.FileName = $exePath
    $pinfo.RedirectStandardInput = $true
    $pinfo.RedirectStandardOutput = $true
    $pinfo.UseShellExecute = $false
    $proc = [System.Diagnostics.Process]::Start($pinfo)
    $proc.StandardInput.Write($inputData)
    $proc.StandardInput.Close()
    $stdOut = $proc.StandardOutput.ReadToEnd()
    $proc.WaitForExit()
    $stdOut | Out-File -FilePath $exeOut -Encoding UTF8

    Write-Host "Posting to Flask at $flaskUrl -> $flaskOut"
    # POST form data to Flask /chart endpoint
    try {
        $form = @{
            name = $s.name
            dob = $s.dob
            tob = $s.tob
            place = $s.place
            lat = $s.lat
            lon = $s.lon
        }
        $resp = Invoke-WebRequest -Uri $flaskUrl -Method POST -Body $form -UseBasicParsing -TimeoutSec 30
        $resp.Content | Out-File -FilePath $flaskOut -Encoding UTF8
    }
    catch {
        Write-Warning "Failed to POST to Flask: $($_.Exception.Message)"
    }

    # Simple diff (textual) - show top 20 differing lines
    Write-Host "Diff (exe vs flask) for $id"
    $exeLines = Get-Content $exeOut
    $flaskLines = Get-Content $flaskOut
    $max = [Math]::Max($exeLines.Length, $flaskLines.Length)
    $differences = @()
    for ($i=0; $i -lt $max; $i++) {
        $a = if ($i -lt $exeLines.Length) { $exeLines[$i] } else { '' }
        $b = if ($i -lt $flaskLines.Length) { $flaskLines[$i] } else { '' }
        if ($a -ne $b) { $differences += "Line $($i+1): EXE: $a`n         FLASK: $b" }
        if ($differences.Count -ge 20) { break }
    }
    if ($differences.Count -eq 0) { Write-Host "No textual differences found (simple compare)." }
    else { $differences | ForEach-Object { Write-Host $_ } }

    Write-Host "Outputs saved to: $exeOut and $flaskOut`n"
}

Write-Host "Done. Review files in $outDir" 
# Run this from the project root: C:\Users\Administrator\Desktop\darukaa
# Scans every text file in the project (excluding .venv, .git, __pycache__,
# knowledge\chroma, and binary sources like PDFs), fixes UTF-16/UTF-8-BOM
# files to clean UTF-8 (no BOM), and validates .py/.json files afterward.

$root = Get-Location
$textExtensions = @(".py", ".json", ".txt", ".md", ".yml", ".yaml", ".toml",
                     ".cfg", ".ini", ".ps1", ".example")
$excludeDirs = @(".venv", ".git", "__pycache__", "chroma", ".pytest_cache")

function Test-ShouldSkip($path) {
    foreach ($dir in $excludeDirs) {
        if ($path -match [regex]::Escape("\$dir\")) { return $true }
    }
    return $false
}

$allFiles = Get-ChildItem -Path $root -Recurse -File | Where-Object {
    (-not (Test-ShouldSkip $_.FullName)) -and
    ($textExtensions -contains $_.Extension -or $_.Name -eq ".gitignore" -or $_.Name -eq ".env.example")
}

Write-Host "Scanning $($allFiles.Count) text files under $root ..."
Write-Host ""

$fixedCount = 0
$okCount = 0
$errorFiles = @()

foreach ($f in $allFiles) {
    $bytes = [System.IO.File]::ReadAllBytes($f.FullName)
    if ($bytes.Length -eq 0) { continue }

    $isUtf16LE = $bytes.Length -ge 2 -and $bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE
    $isUtf16BE = $bytes.Length -ge 2 -and $bytes[0] -eq 0xFE -and $bytes[1] -eq 0xFF
    $isUtf8Bom = $bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF
    $hasNull = $bytes -contains 0

    if ($isUtf16LE -or $isUtf16BE -or $isUtf8Bom) {
        try {
            if ($isUtf16LE) {
                $content = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::Unicode)
            } elseif ($isUtf16BE) {
                $content = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::BigEndianUnicode)
            } else {
                $content = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
            }
            [System.IO.File]::WriteAllText($f.FullName, $content, [System.Text.UTF8Encoding]::new($false))
            Write-Host "FIXED:" $f.FullName.Substring($root.Path.Length + 1)
            $fixedCount++
        } catch {
            Write-Host "ERROR fixing:" $f.FullName "-" $_.Exception.Message
            $errorFiles += $f.FullName
        }
    } elseif ($hasNull) {
        Write-Host "WARNING - null bytes but no BOM detected, needs manual check:" $f.FullName
        $errorFiles += $f.FullName
    } else {
        $okCount++
    }
}

Write-Host ""
Write-Host "--- Summary ---"
Write-Host "Fixed: $fixedCount"
Write-Host "Already clean: $okCount"
Write-Host "Problems needing manual check: $($errorFiles.Count)"
if ($errorFiles.Count -gt 0) {
    $errorFiles | ForEach-Object { Write-Host "  -" $_ }
}

Write-Host ""
Write-Host "--- Validating all .py files compile ---"
$pyFiles = $allFiles | Where-Object { $_.Extension -eq ".py" }
foreach ($p in $pyFiles) {
    $result = & python -m py_compile $p.FullName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "SYNTAX ERROR:" $p.FullName
        Write-Host $result
    }
}
Write-Host "Python syntax check done."

Write-Host ""
Write-Host "--- Validating all .json files parse ---"
$jsonFiles = $allFiles | Where-Object { $_.Extension -eq ".json" }
foreach ($j in $jsonFiles) {
    try {
        Get-Content $j.FullName -Raw | ConvertFrom-Json | Out-Null
    } catch {
        Write-Host "INVALID JSON:" $j.FullName "-" $_.Exception.Message
    }
}
Write-Host "JSON validation done."

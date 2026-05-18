# Shinylive export + záplatování index.html
$APP = $PSScriptRoot
$DOCS = "$APP\docs"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

Write-Host "Exportuji aplikaci..."
shinylive export $APP $DOCS

Write-Host "Kopíruji favicon..."
Copy-Item "$APP\Planet-01-256.png" "$DOCS\Planet-01-256.png" -Force

Write-Host "Zaplata index.html..."
$html = [System.IO.File]::ReadAllText("$DOCS\index.html", [System.Text.Encoding]::UTF8)
$html = $html -replace '<title>Shiny App</title>', '<title>RVP Pruzkumnik</title>'
$faviconTag = '    <link rel="icon" href="Planet-01-256.png" type="image/png" />'
$html = $html -replace '(<link rel="stylesheet" href="./shinylive/style-resets.css" />)', "$faviconTag`n    `$1"
[System.IO.File]::WriteAllText("$DOCS\index.html", $html, $utf8NoBom)

Write-Host "Hotovo!"

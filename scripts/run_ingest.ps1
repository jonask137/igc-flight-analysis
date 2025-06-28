# Allow passing arguments to the Python script
param(
    [string]$StartDate,
    [string]$EndDate,
    [string]$Airport,
    [bool]$RunScraper = $false
)

$projectRoot = "C:\Users\402824\repos\igc-flight-analysis"
$pythonExe = "$projectRoot\.venv\Scripts\python.exe"
$scriptPath = "scripts\ingest_scraped_data.py"

cd $projectRoot

if ($RunScraper) {
    Write-Host "Running scraper to fetch data..."
    & $pythonExe -m scraper.fetcher
}

Write-Host "Running ingestion from $StartDate to $EndDate for airport: $Airport"

# Build argument array
$args = @()
if ($StartDate -ne "") {
    $args += "--start-date"
    $args += $StartDate
}
if ($EndDate -ne "") {
    $args += "--end-date"
    $args += $EndDate
}
if ($Airport -ne "") {
    $args += "--airport"
    $args += $Airport
}

& $pythonExe -m scripts.ingest_scraped_data @args

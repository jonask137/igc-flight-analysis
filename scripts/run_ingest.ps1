# Allow passing arguments to the Python script
param(
    [string]$Date = "",
    [string]$Airport = ""
)

$projectRoot = "C:\Users\402824\repos\igc-flight-analysis"
$pythonExe = "$projectRoot\.venv\Scripts\python.exe"
$scriptPath = "scripts\ingest_scraped_data.py"

cd $projectRoot

# Build argument array
$args = @()
if ($Date -ne "") {
    $args += "--date"
    $args += $Date
}
if ($Airport -ne "") {
    $args += "--airport"
    $args += $Airport
}

& $pythonExe -m scripts.ingest_scraped_data @args

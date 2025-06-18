$projectRoot = "C:\Users\402824\repos\igc-flight-analysis"
$pythonExe = "$projectRoot\.venv\Scripts\python.exe"
$scriptPath = "scripts\ingest_scraped_data.py"

cd $projectRoot
& $pythonExe -m scripts.ingest_scraped_data

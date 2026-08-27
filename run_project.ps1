$ErrorActionPreference = "Stop"

if (Test-Path ".venv\Scripts\python.exe") {
    $ProjectPython = ".venv\Scripts\python.exe"
} else {
    $ProjectPython = "python"
}

& $ProjectPython "scripts\run_pipeline.py" --regenerate
& $ProjectPython -m unittest discover -s tests -v

Write-Host "Pipeline complete. Open reports\figures\executive_dashboard.png or excel\Ecommerce_Analytics_Dashboard.xlsx."


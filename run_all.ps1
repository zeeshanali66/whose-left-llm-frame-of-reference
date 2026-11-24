$proj = "F:\Masters\research-ideas\frame-of-reference-3d"
$p = Start-Process -FilePath "python" -ArgumentList "-I", "$proj\for_pipeline.py", "run" -WorkingDirectory $proj `
     -RedirectStandardOutput "$proj\results\run.log" -RedirectStandardError "$proj\results\run.err" -WindowStyle Hidden -PassThru
Start-Process -FilePath "python" -ArgumentList "-I", "$proj\watchdog.py", $p.Id -WorkingDirectory $proj -WindowStyle Hidden
$p.WaitForExit()
& python -I "$proj\for_pipeline.py" results *> "$proj\results\results.log"
"done $(Get-Date -Format HH:mm)" | Out-File -Append "$proj\results\run.log"

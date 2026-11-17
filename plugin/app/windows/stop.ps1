# Stop the Study Desk server (and the tutor processes it started) on Windows.
#
#   powershell -ExecutionPolicy Bypass -File stop.ps1 [-Port <n>]
#
# It asks the server to shut down, so it only ever stops Study Desk itself.
# The same as: python serve.py --stop
param([int]$Port = 0)
if ($Port -le 0) { $Port = if ($env:STUDY_DESK_PORT) { [int]$env:STUDY_DESK_PORT } else { 8030 } }
$url = "http://127.0.0.1:$Port"
try {
    $health = Invoke-RestMethod "$url/api/health" -TimeoutSec 2
} catch {
    "Study Desk is not running on port $Port."
    exit 0
}
if ($health.app -ne 'study-desk') {
    "Port $Port is in use by something else; nothing stopped."
    exit 1
}
Invoke-RestMethod "$url/api/shutdown" -Method Post -Headers @{ 'X-Study-Desk' = '1' } -TimeoutSec 5 | Out-Null
'Study Desk stopped.'

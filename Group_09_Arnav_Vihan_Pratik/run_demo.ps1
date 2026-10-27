param(
 [ValidateSet('course_climb','course','course_blocked','mission','walk','climb','avoid','blocked','tilt')][string]$Mode='course_climb',
 [switch]$Setup,[switch]$Live,[switch]$Business,[switch]$Record,[switch]$Viewer,[switch]$Tests,
 [string]$Python=''
)
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
if ($Setup) {
 if (!(Test-Path '.venv\Scripts\python.exe')) {
  if ($Python) {
   & $Python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,12) else 1)"
   if ($LASTEXITCODE -ne 0) { throw 'Use a Python 3.12 interpreter.' }
  }
  if ($Python) { & $Python -m venv .venv } else { py -3.12 -m venv .venv }
  if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.12, then rerun -Setup.' }
 }
 & '.\.venv\Scripts\python.exe' -m pip install -r requirements-lock.txt
 if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
$demoPython=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (!(Test-Path $demoPython)) {
 $demoPython=Join-Path (Split-Path $PSScriptRoot) '.venv\Scripts\python.exe'
}
if (!(Test-Path $demoPython)) { throw 'Run .\run_demo.ps1 -Setup first.' }
if ($Business) { & $demoPython analytics\business_dashboard.py; exit $LASTEXITCODE }
if ($Tests) { & $demoPython -m pytest -q; exit $LASTEXITCODE }
if ($Setup -and !($Live -or $Record -or $Viewer)) { Write-Host 'Setup complete.'; exit 0 }
$trialOut='analytics\local_runs\'+$Mode+'_'+(Get-Date -Format yyyyMMdd_HHmmss)
$demoArgs=@('-X','utf8','M20\simulation.py','--mode',$Mode,'--out',$trialOut)
if ($Live) { $demoArgs+='--live' }
if ($Record) { $demoArgs+='--record' }
if ($Viewer) { $demoArgs+='--viewer' }
& $demoPython @demoArgs
exit $LASTEXITCODE

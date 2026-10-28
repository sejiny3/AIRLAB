# AIRLAB 강습회: Windows 노트북 사전 점검 (WSL 설치 전에 실행)
#
#   powershell -ExecutionPolicy Bypass -File check_windows.ps1            # 점검만
#   powershell -ExecutionPolicy Bypass -File check_windows.ps1 -Install   # 점검 + WSL/Ubuntu 설치 (관리자 권한 창에서)
param([switch]$Install)

$ErrorActionPreference = 'SilentlyContinue'
$env:WSL_UTF8 = '1'
$script:fail = 0; $script:warnc = 0
function Pass($m) { Write-Host "  [OK]   $m" -ForegroundColor Green }
function Warn($m) { Write-Host "  [주의] $m" -ForegroundColor Yellow; $script:warnc++ }
function Fail($m) { Write-Host "  [실패] $m" -ForegroundColor Red; $script:fail++ }

Write-Host "`n== Windows" -ForegroundColor Cyan
$os = Get-CimInstance Win32_OperatingSystem
$build = [int]$os.BuildNumber
if ($build -ge 22000) { Pass "$($os.Caption) (빌드 $build)" }
elseif ($build -ge 19044) { Warn "$($os.Caption) (빌드 $build): Windows 10은 동작하지만 Windows 11 권장" }
else { Fail "빌드 $build : WSLg(리눅스 GUI)에는 Windows 10 21H2(19044) 이상이 필요합니다. Windows 업데이트를 먼저 하세요." }

Write-Host "`n== 하드웨어" -ForegroundColor Cyan
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$cores = (Get-CimInstance Win32_Processor | Measure-Object NumberOfLogicalProcessors -Sum).Sum
if ($cores -ge 4) { Pass "CPU $($cpu.Name.Trim()) ($cores 스레드)" } else { Fail "CPU $cores 스레드 (4 이상 필요)" }
$ram = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
if ($ram -ge 16) { Pass "RAM ${ram}GB" } elseif ($ram -ge 8) { Warn "RAM ${ram}GB (16GB 권장, 8GB는 MoveIt+Nav2 동시 실행 시 느림)" } else { Fail "RAM ${ram}GB (8GB 이상 필요)" }
$free = [math]::Round((Get-PSDrive C).Free / 1GB)
if ($free -ge 30) { Pass "C: 여유 ${free}GB" } else { Fail "C: 여유 ${free}GB (30GB 이상 필요)" }
Get-CimInstance Win32_VideoController | ForEach-Object { Pass "GPU $($_.Name) (드라이버 $($_.DriverVersion))" }

$hyp = (Get-CimInstance Win32_ComputerSystem).HypervisorPresent
$virt = $cpu.VirtualizationFirmwareEnabled
if ($hyp) { Pass "가상화 사용 중 (하이퍼바이저 동작)" }
elseif ($virt) { Pass "BIOS 가상화 켜짐" }
else { Fail "BIOS/UEFI에서 가상화(Intel VT-x / AMD SVM)가 꺼져 있습니다. 설치 가이드 '가상화 켜기'를 보세요." }

Write-Host "`n== WSL" -ForegroundColor Cyan
$wslVer = (wsl.exe --version 2>$null) -join "`n"
if ($LASTEXITCODE -eq 0 -and $wslVer) {
  $line = [regex]::Match($wslVer, '\d+\.\d+\.\d+(\.\d+)?').Value
  Pass "WSL 설치됨 (버전 $line)"
  $distros = (wsl.exe -l -q 2>$null) | ForEach-Object { $_.Trim() } | Where-Object { $_ }
  if ($distros -contains 'Ubuntu-22.04') { Pass "Ubuntu-22.04 배포판 있음" }
  else { Warn "Ubuntu-22.04 배포판 없음 (설치된 배포판: $($distros -join ', '))" }
} else {
  Warn "WSL이 아직 설치되지 않았습니다 (정상, 다음 단계에서 설치)"
}

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($Install) {
  Write-Host "`n== 설치" -ForegroundColor Cyan
  if (-not $isAdmin) { Fail "관리자 권한이 아닙니다. 시작 메뉴 > PowerShell 우클릭 > '관리자 권한으로 실행' 후 다시 실행하세요."; exit 1 }
  if ($script:fail -gt 0) { Write-Host "  위 [실패] 항목을 먼저 해결하세요." -ForegroundColor Red; exit 1 }
  wsl.exe --update
  wsl.exe --install -d Ubuntu-22.04
  Write-Host "`n  '재부팅이 필요하다'는 메시지가 나왔다면 재부팅 후, 시작 메뉴에서 'Ubuntu 22.04'를 실행하세요." -ForegroundColor Cyan
  Write-Host "  처음 실행하면 리눅스 사용자 이름/비밀번호를 만듭니다 (비밀번호는 sudo에 쓰니 꼭 기억하세요)." -ForegroundColor Cyan
}

Write-Host ""
if ($script:fail -gt 0) { Write-Host "결과: 실패 $($script:fail)개, 주의 $($script:warnc)개. 실패 항목을 해결해야 실습할 수 있습니다." -ForegroundColor Red }
else { Write-Host "결과: 실습 가능 (주의 $($script:warnc)개)" -ForegroundColor Green }

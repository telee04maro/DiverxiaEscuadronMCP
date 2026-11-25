<#
  Asistente de WhatsApp del hackathon: SUSTITUIR la clave de BALTER por la de la empresa de la DEMO.
  - Para antes el asistente (-Parar) si estuviera en marcha.
  - Borra la clave anterior de la demo y pide la nueva (no se ve al pegarla).
  - Se niega si es igual a alguna clave de produccion protegida (HACK_PROTEGER_CLAVES en el .env local).
  - Comprueba que el catalogo de esa empresa tiene el ARTICULO DE CONTROL (que solo existe en la empresa
    de la demo) y lo guarda en config.json: el ciclo lo vuelve a comprobar antes de hacer nada.
  Uso:  powershell -ExecutionPolicy Bypass -File .\whatsapp-hack\HACK-ClaveBalter.ps1
#>
$ErrorActionPreference = 'Stop'
$base = Join-Path $env:LOCALAPPDATA 'HACK-WhatsApp'
$ciclo = Join-Path $base 'ciclo'
$ruta = Join-Path $base 'claves\balter.dpapi'
$cfgPath = Join-Path $ciclo 'config.json'
function Write-Ok($t) { Write-Host "[OK] $t" -ForegroundColor Green }
function Stop-Script($t) { Write-Host "[PARADO] $t" -ForegroundColor Red; exit 1 }
function Get-Plano([Security.SecureString]$s) { return (New-Object System.Net.NetworkCredential('', $s)).Password }
function Read-Dpapi([string]$Ruta) {
    if (-not (Test-Path -LiteralPath $Ruta)) { return $null }
    try { $s = ConvertTo-SecureString -String ((Get-Content -LiteralPath $Ruta -Encoding UTF8 -TotalCount 1).Trim()); try { return Get-Plano $s } finally { $s.Dispose() } } catch { return $null }
}

# Claves de PRODUCCION de este equipo que nunca deben usarse en la demo. Las carpetas (dentro de
# %LOCALAPPDATA%) se indican en el .env local del repositorio (HACK_PROTEGER_CLAVES, separadas por ;),
# que no se sube a git. Asi el repositorio no contiene ningun dato de la instalacion de produccion.
function Get-EnvRepo([string]$Clave) {
    $f = Join-Path (Split-Path $PSScriptRoot -Parent) '.env'
    if (-not (Test-Path -LiteralPath $f)) { return '' }
    foreach ($l in [IO.File]::ReadAllLines($f)) { if ($l -match ('^\s*' + [regex]::Escape($Clave) + '\s*=(.*)$')) { return $Matches[1].Trim() } }
    return ''
}
function Get-ListaEnv([string]$Clave) { return @((Get-EnvRepo $Clave) -split ';' | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }
function Get-ClavesProduccion {
    $l = @()
    foreach ($d in (Get-ListaEnv 'HACK_PROTEGER_CLAVES')) {
        $dir = Join-Path $env:LOCALAPPDATA $d
        if (Test-Path -LiteralPath $dir) { foreach ($f in @(Get-ChildItem -LiteralPath $dir -Filter '*.dpapi' -ErrorAction SilentlyContinue)) { $v = Read-Dpapi $f.FullName; if ($v) { $l += $v.Trim() } } }
    }
    return $l
}
# Comprueba que el catalogo de la empresa de la clave tiene el articulo de control (solo existe en la empresa de la demo).
function Test-ArticuloControl([string]$Clave, [string]$Articulo) {
    $cuerpo = [Text.Encoding]::UTF8.GetBytes((@{ action = 'search'; name = $Articulo; limit = 25 } | ConvertTo-Json -Compress))
    $b = Invoke-RestMethod -Uri 'https://app.balter.es/api/v1/articles.php' -Method Post -Body $cuerpo -ContentType 'application/json; charset=utf-8' -Headers @{ Authorization = 'Bearer ' + $Clave } -TimeoutSec 30
    if ([string]$b.status -cne 'success') { return $false }
    foreach ($a in @($b.data.articles)) { if ([string]$a.name -ceq $Articulo) { return $true } }
    return $false
}

cls
Write-Host '=== CAMBIAR LA CLAVE DE BALTER DE LA DEMO ===' -ForegroundColor Cyan
if (-not (Test-Path -LiteralPath $cfgPath)) { Stop-Script 'No existe la instalacion de la demo: ejecuta antes HACK-Instalar.ps1.' }
$cfg = Get-Content -LiteralPath $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
# Parada: el bucle lee esta marca en cada vuelta y se detiene; la tarea programada queda desactivada.
$cfg.automatico_habilitado = $false
[IO.File]::WriteAllText($cfgPath, ($cfg | ConvertTo-Json -Depth 20), (New-Object Text.UTF8Encoding($false)))
$t = Get-ScheduledTask -TaskName 'HACK WhatsApp - Demo' -ErrorAction SilentlyContinue
if ($t) { Disable-ScheduledTask -TaskName 'HACK WhatsApp - Demo' | Out-Null }
Write-Ok 'Asistente de la demo PARADO'
if (Test-Path -LiteralPath $ruta) { Remove-Item -LiteralPath $ruta -Force; Write-Ok 'Clave anterior de la demo eliminada' }

$plano = (Get-Plano (Read-Host 'Pega la clave de BALTER de la empresa de la DEMO (no se vera) y pulsa Intro' -AsSecureString)).Trim()
if ([string]::IsNullOrWhiteSpace($plano)) { Stop-Script 'Clave vacia: no se ha guardado nada. El asistente no puede crear fichas sin clave.' }
if ((Get-ClavesProduccion) -ccontains $plano) { Stop-Script 'Esa clave es una de las claves de PRODUCCION protegidas de este equipo. No se guarda.' }

# Se muestran los articulos del catalogo de la empresa de ESA clave (solo nombres, sin datos personales)
# para elegir uno que solo exista en la empresa de la demo.
try {
    $cuerpo = [Text.Encoding]::UTF8.GetBytes('{"action":"search","limit":100}')
    $b = Invoke-RestMethod -Uri 'https://app.balter.es/api/v1/articles.php' -Method Post -Body $cuerpo -ContentType 'application/json; charset=utf-8' -Headers @{ Authorization = 'Bearer ' + $plano } -TimeoutSec 30
} catch { Stop-Script ('BALTER no acepta la clave: ' + $_.Exception.Message) }
if ([string]$b.status -cne 'success') { Stop-Script 'BALTER no devolvio el catalogo.' }
$nombres = @(@($b.data.articles) | ForEach-Object { [string]$_.name } | Where-Object { $_ } | Sort-Object -Unique)
if ($nombres.Count -eq 0) { Stop-Script 'El catalogo de la empresa de esa clave esta vacio: crea en BALTER (empresa de la demo) un articulo, por ejemplo "Demo Vigia", y repite.' }
Write-Host ''
Write-Host "Catalogo de la empresa de ESTA clave ($($nombres.Count) articulos):" -ForegroundColor Cyan
for ($i = 0; $i -lt $nombres.Count; $i++) { Write-Host ('  ' + ($i + 1) + ') ' + $nombres[$i]) }
Write-Host ''
Write-Host 'Si reconoces aqui el catalogo de una empresa REAL, la clave NO es la de la demo: pulsa Intro para cancelar.' -ForegroundColor Yellow
$sel = Read-Host 'Numero del articulo que SOLO existe en la empresa de la demo (Intro = cancelar)'
$n = 0
if (-not [int]::TryParse($sel, [ref]$n) -or $n -lt 1 -or $n -gt $nombres.Count) { Stop-Script 'Cancelado: no se guarda nada.' }
$art = $nombres[$n - 1]
Write-Ok "La empresa de la clave tiene el articulo de control '$art'"
if ((Read-Host 'Escribe DEMO si la clave es de la empresa FICTICIA de la demo y no de una empresa real') -cne 'DEMO') { Stop-Script 'Sin confirmacion: no se guarda.' }

$s = ConvertTo-SecureString -String $plano -AsPlainText -Force
try { Set-Content -LiteralPath $ruta -Value (ConvertFrom-SecureString $s) -Encoding UTF8 } finally { $s.Dispose() }
$plano = $null
if ($null -eq $cfg.PSObject.Properties['balter_control_articulo']) { $cfg | Add-Member -NotePropertyName 'balter_control_articulo' -NotePropertyValue $art.Trim() }
else { $cfg.balter_control_articulo = $art.Trim() }
[IO.File]::WriteAllText($cfgPath, ($cfg | ConvertTo-Json -Depth 20), (New-Object Text.UTF8Encoding($false)))
Write-Ok 'Clave nueva guardada cifrada y articulo de control guardado en config.json'
Write-Host ''
Write-Host 'El asistente esta PARADO. Para volver a arrancarlo:' -ForegroundColor Yellow
Write-Host ('  powershell -ExecutionPolicy Bypass -File "' + (Join-Path $ciclo 'HACK-Ciclo.ps1') + '" -ActivarFondo -Segundos 10')

<#
  Asistente de WhatsApp del hackathon: INSTALACION de la instancia de demostracion.

  Que hace:
  - Copia el ciclo a %LOCALAPPDATA%\HACK-WhatsApp\ciclo (fuera de OneDrive y de git).
  - Guarda las claves cifradas con DPAPI en %LOCALAPPDATA%\HACK-WhatsApp\claves.
  - Se niega si una clave es igual a alguna de las claves de produccion protegidas del equipo.
  - Comprueba con Zernio que la clave solo ve UN numero de WhatsApp y que es el de la demo.
  - Comprueba que la clave de BALTER es de la empresa de la demo (articulo de control del catalogo).
  - Crea el perfil de Hermes 'hackaton-demo' (vacio) con su SOUL.md.

  Si en este equipo hay una instalacion de produccion, se indica en el .env LOCAL del repositorio
  (no se sube a git), separando varios valores con ';':
    HACK_PROTEGER_CLAVES   carpetas de %LOCALAPPDATA% con claves .dpapi de produccion
    HACK_PROTEGER_CICLO    carpeta de %LOCALAPPDATA% del ciclo de produccion (con su config.json)
    HACK_PROTEGER_MUTEX    mutex del ciclo de produccion
    HACK_PROTEGER_PERFIL   perfil de Hermes de produccion

  Uso (PowerShell, en la carpeta del repositorio, rama Miguel):
    powershell -ExecutionPolicy Bypass -File .\whatsapp-hack\HACK-Instalar.ps1
#>
$ErrorActionPreference = 'Stop'
$origen = $PSScriptRoot
$base = Join-Path $env:LOCALAPPDATA 'HACK-WhatsApp'
$ciclo = Join-Path $base 'ciclo'
$claves = Join-Path $base 'claves'
$numeroDemo = '607145471'
$perfil = 'hackaton-demo'

function Write-Ok($t) { Write-Host "[OK] $t" -ForegroundColor Green }
function Write-Aviso($t) { Write-Host "[!]  $t" -ForegroundColor Yellow }
function Stop-Instalacion($t) { Write-Host "[PARADO] $t" -ForegroundColor Red; exit 1 }
function Read-Frase([string]$Frase, [string]$Pregunta) { return ((Read-Host $Pregunta) -ceq $Frase) }
function Get-Plano([Security.SecureString]$s) { return (New-Object System.Net.NetworkCredential('', $s)).Password }
function Read-Dpapi([string]$Ruta) {
    if (-not (Test-Path -LiteralPath $Ruta)) { return $null }
    try {
        $s = ConvertTo-SecureString -String ((Get-Content -LiteralPath $Ruta -Encoding UTF8 -TotalCount 1).Trim())
        try { return Get-Plano $s } finally { $s.Dispose() }
    } catch { return $null }
}
function Save-Dpapi([string]$Ruta, [string]$Plano) {
    $s = ConvertTo-SecureString -String $Plano -AsPlainText -Force
    try { Set-Content -LiteralPath $Ruta -Value (ConvertFrom-SecureString $s) -Encoding UTF8 } finally { $s.Dispose() }
}
function Get-EnvRepo([string]$Clave) {
    $f = Join-Path (Split-Path $PSScriptRoot -Parent) '.env'
    if (-not (Test-Path -LiteralPath $f)) { return '' }
    foreach ($l in [IO.File]::ReadAllLines($f)) { if ($l -match ('^\s*' + [regex]::Escape($Clave) + '\s*=(.*)$')) { return $Matches[1].Trim() } }
    return ''
}
function Get-ListaEnv([string]$Clave) { return @((Get-EnvRepo $Clave) -split ';' | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }
# Claves de PRODUCCION de este equipo que nunca deben usarse en la demo. Las carpetas (dentro de
# %LOCALAPPDATA%) se indican en el .env local del repositorio (HACK_PROTEGER_CLAVES, separadas por ;),
# que no se sube a git. Asi el repositorio no contiene ningun dato de la instalacion de produccion.
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
function Get-Clave([string]$Nombre, [string]$VariableEnv, [string]$Fichero, [string[]]$Produccion) {
    $ruta = Join-Path $claves $Fichero
    $plano = $null
    if (Test-Path -LiteralPath $ruta) {
        if (-not (Read-Frase 'REEMPLAZAR' "Ya hay una clave de $Nombre guardada. Escribe REEMPLAZAR para cambiarla (Intro = conservarla)")) {
            $plano = Read-Dpapi $ruta
            if ($plano) { Write-Ok "Se conserva la clave de $Nombre"; return $plano }
        }
    }
    $env1 = $(if ($Nombre -eq 'BALTER') { '' } else { Get-EnvRepo $VariableEnv })
    if ($env1 -and (Read-Frase 'USAR' "Hay una clave de $Nombre en el .env del repositorio. Escribe USAR para usarla (Intro = pegar otra)")) { $plano = $env1 }
    if (-not $plano) { $plano = (Get-Plano (Read-Host "Pega la clave de $Nombre de la DEMO (no se vera) y pulsa Intro" -AsSecureString)).Trim() }
    if ([string]::IsNullOrWhiteSpace($plano)) { Stop-Instalacion "Clave de $Nombre vacia." }
    if ((Get-ClavesProduccion) -ccontains $plano) { Stop-Instalacion "Esa clave de $Nombre es una de las claves de PRODUCCION protegidas de este equipo. Usa la de la demo." }
    Save-Dpapi $ruta $plano
    Write-Ok "Clave de $Nombre guardada cifrada ($($plano.Length) caracteres)"
    return $plano
}

cls
Write-Host '=== ASISTENTE WHATSAPP (HACKATHON) - INSTALACION ===' -ForegroundColor Cyan
Write-Host 'Instancia de DEMOSTRACION: usa su propia carpeta, claves, perfil de Hermes, mutex y tarea programada.'
$prodCiclo = @(Get-ListaEnv 'HACK_PROTEGER_CICLO') | Select-Object -First 1
if (-not (Get-EnvRepo 'HACK_PROTEGER_CLAVES')) { Write-Aviso 'El .env no indica claves de produccion a proteger (HACK_PROTEGER_CLAVES). Si en este equipo hay una instalacion de produccion, anadelas antes.' }
if ($origen.ToLowerInvariant().StartsWith((Join-Path $env:LOCALAPPDATA 'hermes').ToLowerInvariant())) { Stop-Instalacion 'Ejecuta este script desde el repositorio, no desde la carpeta de Hermes.' }
foreach ($d in @($base, $ciclo, $claves)) { if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null } }

# 1. Codigo (solo los scripts; nunca config.json ni estado).
foreach ($f in @('HACK-Ciclo.ps1', 'HACK-Ciclo-Lib.ps1', 'HACK-Ciclo-Pruebas.ps1', 'HACK-Ciclo-Oculto.vbs', 'HACK-Bucle-Oculto.vbs', 'HACK-ClaveBalter.ps1', 'config.ejemplo.json', 'SOUL-hackaton-demo.md')) {
    Copy-Item -LiteralPath (Join-Path $origen $f) -Destination (Join-Path $ciclo $f) -Force
}
Write-Ok "Ciclo copiado en $ciclo"

# 2. Claves (DPAPI, solo para este usuario de Windows).
Write-Host ''
Write-Host '--- Claves de la DEMO ---' -ForegroundColor Cyan
$zernio = Get-Clave 'Zernio' 'ZERNIO_API_KEY' 'zernio.dpapi' @()
$balter = Get-Clave 'BALTER' 'BALTER_TOKEN' 'balter.dpapi' @()

# 3. Zernio: una sola cuenta de WhatsApp y que sea la de la demo.
Write-Host ''
Write-Host '--- Comprobando Zernio (solo lectura) ---' -ForegroundColor Cyan
try { $r = Invoke-RestMethod -Uri 'https://zernio.com/api/v1/accounts?platform=whatsapp' -Headers @{ Authorization = 'Bearer ' + $zernio } -TimeoutSec 30 }
catch { Stop-Instalacion ('Zernio no acepta la clave o no responde: ' + $_.Exception.Message) }
$cuentas = @(@($r.accounts) | Where-Object { $null -ne $_ })
if ($cuentas.Count -ne 1) { Stop-Instalacion "La clave de Zernio ve $($cuentas.Count) cuentas de WhatsApp. La demo necesita una cuenta de Zernio con UN solo numero (el de la demo)." }
$json = $cuentas[0] | ConvertTo-Json -Depth 10
if (-not [regex]::IsMatch($json, '607\D{0,2}14\D{0,2}5\D{0,2}4\D{0,2}71')) { Stop-Instalacion "La cuenta de Zernio no es el numero de la demo (+34 $numeroDemo)." }
$cuenta = [string]$cuentas[0]._id; if (-not $cuenta) { $cuenta = [string]$cuentas[0].id }
if (-not $cuenta) { Stop-Instalacion 'No se encuentra el identificador de la cuenta de Zernio.' }
$prodCfg = $null
if ($prodCiclo -and (Test-Path -LiteralPath (Join-Path (Join-Path $env:LOCALAPPDATA $prodCiclo) 'config.json'))) { $prodCfg = Get-Content -LiteralPath (Join-Path (Join-Path $env:LOCALAPPDATA $prodCiclo) 'config.json') -Raw -Encoding UTF8 | ConvertFrom-Json }
if ($prodCfg -and [string]$prodCfg.account_id -ceq $cuenta) { Stop-Instalacion 'Es la cuenta de Zernio de la instalacion de PRODUCCION protegida.' }
Write-Ok "Zernio: una sola cuenta, numero de la demo (****$($numeroDemo.Substring(5))), cuenta $cuenta"

# 4. BALTER: lectura de un articulo del catalogo.
Write-Host ''
Write-Host '--- Comprobando BALTER (solo lectura del catalogo) ---' -ForegroundColor Cyan
try {
    $cuerpo = [Text.Encoding]::UTF8.GetBytes('{"action":"search","limit":1}')
    $b = Invoke-RestMethod -Uri 'https://app.balter.es/api/v1/articles.php' -Method Post -Body $cuerpo -ContentType 'application/json' -Headers @{ Authorization = 'Bearer ' + $balter } -TimeoutSec 30
    if ([string]$b.status -cne 'success') { throw 'respuesta sin status success' }
    Write-Ok 'BALTER: la clave funciona (lectura del catalogo)'
} catch { Stop-Instalacion ('BALTER no acepta la clave: ' + $_.Exception.Message) }
Write-Aviso 'La clave de BALTER decide en que empresa se crean las oportunidades.'
Write-Host 'Articulo de control: el nombre EXACTO de un articulo o servicio que solo exista en el catalogo de la empresa de la demo.'
$artDefecto = ''
$cfgPrevio = Join-Path $ciclo 'config.json'
if (Test-Path -LiteralPath $cfgPrevio) { $artDefecto = [string](Get-Content -LiteralPath $cfgPrevio -Raw -Encoding UTF8 | ConvertFrom-Json).balter_control_articulo }
if (-not $artDefecto) { Stop-Instalacion 'Primero ejecuta HACK-ClaveBalter.ps1 para guardar la clave de la demo y elegir el articulo de control.' }
$artControl = Read-Host "Articulo de control [$artDefecto]"
if ([string]::IsNullOrWhiteSpace($artControl)) { $artControl = $artDefecto }
$artControl = $artControl.Trim()
if (-not (Test-ArticuloControl $balter $artControl)) { Stop-Instalacion "El catalogo de la empresa de esa clave NO tiene el articulo '$artControl': no es la empresa de la demo. Ejecuta HACK-ClaveBalter.ps1 con la clave correcta." }
Write-Ok "La empresa de la clave tiene el articulo de control '$artControl'"
if (-not (Read-Frase 'DEMO' 'Escribe DEMO si la clave es de la empresa FICTICIA de la demo y no de una empresa real')) { Stop-Instalacion 'Sin confirmacion de la empresa de la demo.' }
$zernio = $null; $balter = $null

# 5. Perfil de Hermes propio (vacio: sin memoria de otros perfiles).
Write-Host ''
Write-Host '--- Perfil de Hermes de la demo ---' -ForegroundColor Cyan
if (-not (Get-Command hermes -ErrorAction SilentlyContinue)) { Stop-Instalacion 'No se encuentra el comando hermes.' }
$lista = (@(& hermes profile list 2>&1) | ForEach-Object { [string]$_ }) -join "`n"
if ($lista -notmatch [regex]::Escape($perfil)) {
    & hermes profile create $perfil
    if ($LASTEXITCODE -ne 0) { Stop-Instalacion "No se pudo crear el perfil $perfil de Hermes." }
    Write-Ok "Perfil de Hermes '$perfil' creado"
} else { Write-Ok "El perfil de Hermes '$perfil' ya existe" }
$dirPerfil = Join-Path $env:LOCALAPPDATA "hermes\profiles\$perfil"
if (Test-Path -LiteralPath $dirPerfil) {
    Copy-Item -LiteralPath (Join-Path $origen 'SOUL-hackaton-demo.md') -Destination (Join-Path $dirPerfil 'SOUL.md') -Force
    Write-Ok "SOUL.md de la demo copiado en $dirPerfil"
} else { Write-Aviso "No encuentro ${dirPerfil}: copia a mano SOUL-hackaton-demo.md como SOUL.md del perfil $perfil." }
Write-Host 'Probando Hermes (puede tardar unos segundos)...'
$env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUTF8 = '1'
$pref = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
$prueba = (@(& hermes -p $perfil chat --oneshot --quiet --toolsets clarify --max-turns 1 --query 'Responde solo con la palabra OK_VIGIA' 2>&1) | ForEach-Object { [string]$_ }) -join "`n"
$ErrorActionPreference = $pref
if ($prueba -match 'OK_VIGIA') { Write-Ok 'Hermes responde con el perfil de la demo' }
else { Write-Aviso ('Hermes no devolvio lo esperado. Revisa el modelo del perfil con: hermes -p ' + $perfil + ' setup model') ; Write-Host $prueba }

# 6. config.json de la instancia (solo si no existe; se conserva el estado de la demo).
$cfgPath = Join-Path $ciclo 'config.json'
if (Test-Path -LiteralPath $cfgPath) {
    $cfg = Get-Content -LiteralPath $cfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $cfg.account_id = $cuenta
    Write-Ok 'config.json existente: se actualizan account_id y el articulo de control'
} else {
    $cfg = Get-Content -LiteralPath (Join-Path $origen 'config.ejemplo.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $cfg.account_id = $cuenta
    Write-Ok 'config.json creado a partir de config.ejemplo.json'
}
$proteger = [pscustomobject]@{ carpeta_ciclo = @(Get-ListaEnv 'HACK_PROTEGER_CICLO'); mutex = @(Get-ListaEnv 'HACK_PROTEGER_MUTEX'); perfil_hermes = @(Get-ListaEnv 'HACK_PROTEGER_PERFIL') }
if ($null -eq $cfg.PSObject.Properties['proteger']) { $cfg | Add-Member -NotePropertyName 'proteger' -NotePropertyValue $proteger } else { $cfg.proteger = $proteger }
if (@($proteger.mutex) -contains [string]$cfg.mutex -or @($proteger.perfil_hermes) -contains [string]$cfg.perfil_hermes) { Stop-Instalacion 'config.json usa el mutex o el perfil de Hermes de produccion.' }
if ($null -eq $cfg.PSObject.Properties['balter_control_articulo']) { $cfg | Add-Member -NotePropertyName 'balter_control_articulo' -NotePropertyValue $artControl }
else { $cfg.balter_control_articulo = $artControl }
[IO.File]::WriteAllText($cfgPath, ($cfg | ConvertTo-Json -Depth 20), (New-Object Text.UTF8Encoding($false)))

Write-Host ''
Write-Host 'INSTALACION TERMINADA. Siguiente paso: pruebas sin conexion:' -ForegroundColor Green
Write-Host ('  & "' + (Join-Path $ciclo 'HACK-Ciclo-Pruebas.ps1') + '"')

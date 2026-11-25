<#
  Prueba de INTEGRACION del asistente con el ERP de demo de Vigia, de verdad por HTTP.
  WhatsApp (Zernio) y Hermes se simulan; la API del ERP es la real (vigia.connectors.http_api).
  La lanza tests/test_whatsapp_bot.py, que arranca la API con una base de datos temporal.
  Uso: $env:VIGIA_ERP_TOKEN = '...'; .\HACK-Ciclo-Integracion.ps1 -Url http://127.0.0.1:8765/api/v1 -Raiz <carpeta temporal>
  Devuelve, en la ultima linea, un JSON con el estado de cada conversacion.
#>
param(
    [Parameter(Mandatory = $true)][string]$Url,
    [Parameter(Mandatory = $true)][string]$Raiz
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'HACK-Ciclo-Lib.ps1')
if ([string]::IsNullOrWhiteSpace($env:VIGIA_ERP_TOKEN)) { throw 'FALTA_VIGIA_ERP_TOKEN' }

$script:CUENTA = 'acc-integracion'
$script:Z = @{ conv = @{}; posts = 0 }
function Get-WAToken([string]$Nombre) {
    if ($Nombre -eq 'vigia') { return $env:VIGIA_ERP_TOKEN }
    return 'sin-uso'
}
function Get-WAWebhook { return $null }
function New-Conv([string]$Id, [string]$Tel) { $script:Z.conv[$Id] = @{ tel = $Tel; msgs = New-Object System.Collections.ArrayList } }
function Add-Msg([string]$Id, [string]$Dir, [string]$Texto, [string]$Via = $null, [string]$Fuente = $null) {
    $m = [pscustomobject]@{ id = 'wamid.' + [guid]::NewGuid().ToString('N'); direction = $Dir; message = $Texto
        createdAt = (Get-WAAhora).ToString('o'); sentVia = $Via; source = $Fuente }
    [void]$script:Z.conv[$Id].msgs.Add($m); Start-Sleep -Milliseconds 20; return $m
}
function Invoke-WAZernioGet([string]$Ruta) {
    if ($Ruta -match '^/inbox/conversations\?') {
        $data = foreach ($k in $script:Z.conv.Keys) {
            [pscustomobject]@{ id = $k; accountId = $script:CUENTA; platform = 'whatsapp'; updatedTime = $script:Z.conv[$k].msgs[-1].createdAt }
        }
        return [pscustomobject]@{ data = @($data); pagination = [pscustomobject]@{ hasMore = $false }; meta = [pscustomobject]@{ accountsFailed = 0 } }
    }
    if ($Ruta -match '^/inbox/conversations/([^/?]+)/messages\?.*limit=(\d+)') {
        $ms = @($script:Z.conv[$Matches[1]].msgs | Sort-Object { [DateTimeOffset]::Parse($_.createdAt) } -Descending | Select-Object -First ([int]$Matches[2]))
        return [pscustomobject]@{ messages = $ms; pagination = [pscustomobject]@{ hasMore = $false } }
    }
    if ($Ruta -match '^/inbox/conversations/([^/?]+)\?') {
        $id = $Matches[1]
        return [pscustomobject]@{ data = [pscustomobject]@{ id = $id; accountId = $script:CUENTA; platform = 'whatsapp'; isGroup = $false; participantId = $script:Z.conv[$id].tel } }
    }
    throw "Ruta no simulada: $Ruta"
}
function Invoke-WAZernioEnviar([string]$Conversacion, [string]$Texto, [string]$ClaveIdem) {
    $script:Z.posts++
    $m = Add-Msg $Conversacion 'outgoing' $Texto 'api' 'cloudapi'
    return @{ ok = $true; status = 200; incierto = $false; data = [pscustomobject]@{ success = $true; data = [pscustomobject]@{ conversationId = $Conversacion; messageId = $m.id } } }
}
# Hermes simulado: extrae lo que el contacto escribio, igual que se le pide al real.
function Invoke-WAHermes([string]$Prompt) {
    $conv = $Prompt.Substring($Prompt.IndexOf('=== CONVERSACION ==='))
    $contacto = (($conv -split "`n") | Where-Object { $_ -match '\] CONTACTO: ' }) -join "`n"
    $email = $null; if ($contacto -match '([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})') { $email = $Matches[1] }
    $nombre = $null; if ($contacto -match 'Me llamo ([A-Za-z]+ [A-Za-z]+ [A-Za-z]+)') { $nombre = $Matches[1] }
    $resp = if ($nombre -and $email) { 'Gracias. Una persona del equipo de Vigia revisara tu consulta y te contestara pronto.' }
            else { 'Gracias por escribir a Vigia. Para que te contacte el equipo, indicanos tu nombre con apellidos y un correo.' }
    return ([pscustomobject]@{ respuesta = $resp; idioma = 'es'; nombre_completo = $nombre; email = $email; servicio = 'Demo de Vigia para una clinica'
        resumen = 'Quiere ver una demo de Vigia para su clinica.'; requiere_humano = $false; motivo_humano = $null } | ConvertTo-Json -Compress)
}

New-Item -ItemType Directory -Path $Raiz -Force | Out-Null
$cfg = [ordered]@{ schema = 'wa_ciclo_config_v1'; modo = 'produccion'; account_id = $script:CUENTA
    erp = [pscustomobject]@{ tipo = 'vigia'; url = $Url }
    conversaciones_prueba = @(); inicio_produccion_utc = (Get-WAAhora).AddMinutes(-5).ToString('o')
    max_respuestas_por_conversacion = 4; limite_mensajes_mes = 2000; automatico_habilitado = $true
    prefijo_prueba = 'HTEST'; deteccion_prueba_automatica = $true; etiqueta = 'Asistente Virtual Vigia:'
    mutex = 'Local\HACK_Integracion_Ciclo'; empresa = [pscustomobject]@{ nombre = 'Vigia'; quien_contacta = 'una persona del equipo de Vigia' } }
Write-WAJson (Join-Path $Raiz 'config.json') ([pscustomobject]$cfg)

function Invoke-Ciclo { $null = @(Invoke-WACiclo $Raiz $true $true) }
New-Conv 'prueba' '34600000001'; New-Conv 'publico' '34600000002'
Add-Msg 'prueba' 'incoming' 'HTEST: Hola, quiero una demo para mi clinica.' | Out-Null
Add-Msg 'publico' 'incoming' 'Hola, me interesa Vigia.' | Out-Null
Invoke-Ciclo
Add-Msg 'prueba' 'incoming' 'Me llamo Carla Ruiz Sol y mi correo es carla.htest@example.com' | Out-Null
Add-Msg 'publico' 'incoming' 'Me llamo Pablo Diaz Mar y mi correo es pablo.demo@example.com' | Out-Null
Invoke-Ciclo
Invoke-Ciclo; Invoke-Ciclo  # ciclos de mas: no deben duplicar nada

$script:WA.Raiz = $Raiz
$salida = [ordered]@{ posts = $script:Z.posts }
foreach ($id in @('prueba', 'publico')) {
    $e = Get-WAEstadoConv $id
    $salida[$id] = [ordered]@{ estado = $e.estado; opportunity_id = $e.opportunity_id; respuestas = $e.respuestas_enviadas; motivo = $e.motivo }
}
Write-Output ($salida | ConvertTo-Json -Compress -Depth 5)

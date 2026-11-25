<#
  Pruebas del ciclo PARAMETRIZABLE (hackathon), SIN conexion a Zernio, BALTER ni Hermes.
  1-30: las pruebas del ciclo de produccion (garantias contra duplicados, relevo humano, avisos...).
  31-33: la instancia del hackathon (HTEST, etiqueta y empresa propias).
  Simula los tres servicios en memoria (incluidos fallos y timeouts) y comprueba que:
  - nunca se crea una oportunidad duplicada,
  - nunca se responde a clientes existentes ni a chats atendidos por una persona,
  - un resultado incierto nunca se repite a ciegas.
  Ejecutar:  & "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo-Pruebas.ps1"
#>
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'HACK-Ciclo-Lib.ps1')
# Las pruebas usan su propio mutex: nunca bloquean al asistente que este en marcha en este equipo.
$script:WAInstancia.mutex = 'Local\HACK_Pruebas_Ciclo'

$script:T = @{ ok = 0; fallos = @() }
function Check([bool]$c, [string]$txt) {
    if ($c) { $script:T.ok++; Write-Host "  [OK] $txt" -ForegroundColor Green }
    else { $script:T.fallos += $txt; Write-Host "  [FALLO] $txt" -ForegroundColor Red }
}

# ------------------------------------------------------------ mundo simulado
$script:CUENTA = 'acc000000000000000000001'
$script:PRUEBA = 'convhtest00000000000001'
function Reset-Mundo {
    $script:Reloj = [DateTimeOffset]::Parse('2026-11-10T09:00:00Z')
    $script:Z = @{ conv = @{}; posts = 0; fallarPost = $null; alLeer = $null }
    $script:B = @{ personas = @(); altas = 0; fallarAlta = $null; articulos = @('Articulo control pruebas') }
    $script:V = @{ contactos = @(); altas = 0; ultima = $null; fallar = $null; caido = $false; rutaMala = $false }
    $script:WAEmpresaVerificada = $null
    $script:H = @{ llamadas = 0; forzar = $null }
    $script:WA.Contadores = @{ GET = 0; POST = 0; BALTER_LECTURAS = 0; BALTER_ALTAS = 0; HERMES = 0; AVISOS = 0 }
    $script:WA.Avisos.Clear()
    $script:AV = @{ enviados = New-Object System.Collections.ArrayList; fallar = $false; url = 'https://aviso.falso' }
    $script:Raiz = Join-Path ([IO.Path]::GetTempPath()) ('waciclo-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $script:Raiz | Out-Null
}
function New-Conv([string]$Id, [string]$Tel) { $script:Z.conv[$Id] = @{ tel = $Tel; msgs = New-Object System.Collections.ArrayList } }
function Add-Msg([string]$Id, [string]$Dir, [string]$Texto, [int]$MinDesdeAhora = 0, [string]$Via = $null, [string]$Fuente = $null) {
    $c = $script:Z.conv[$Id]
    $m = [pscustomobject]@{ id = 'wamid.' + [guid]::NewGuid().ToString('N'); direction = $Dir; message = $Texto
        createdAt = $script:Reloj.AddMinutes($MinDesdeAhora).ToString('o'); sentVia = $Via; source = $Fuente }
    [void]$c.msgs.Add($m); return $m
}
function Set-Config([string]$Modo, [hashtable]$Extra = @{}) {
    $cfg = [ordered]@{ schema = 'wa_ciclo_config_v1'; modo = $Modo; account_id = $script:CUENTA
        conversaciones_prueba = @($script:PRUEBA); sesion_prueba_inicio_utc = $script:Reloj.AddHours(-1).ToString('o')
        inicio_produccion_utc = $script:Reloj.AddDays(-1).ToString('o'); max_respuestas_por_conversacion = 3
        limite_mensajes_mes = 2000; automatico_habilitado = $true
        # Las pruebas 1-36 son las del ciclo de produccion, contra BALTER (con permiso y articulo de control).
        erp = [pscustomobject]@{ tipo = 'balter' }; balter_autorizado_por = 'Pruebas sin conexion'
        balter_control_articulo = 'Articulo control pruebas' }
    foreach ($k in $Extra.Keys) { $cfg[$k] = $Extra[$k] }
    Write-WAJson (Join-Path $script:Raiz 'config.json') ([pscustomobject]$cfg)
}
$script:PasoMin = 5
function Ciclo([bool]$Ejecutar = $true) {
    $script:Reloj = $script:Reloj.AddMinutes($script:PasoMin)
    return @(Invoke-WACiclo $script:Raiz $Ejecutar $true)
}
function EstadoDe([string]$Id) { $script:WA.Raiz = $script:Raiz; return (Get-WAEstadoConv $Id) }

# ------------------------------------------------------------ dobles de los servicios
function Get-WAAhora { return $script:Reloj }
function Get-WAToken([string]$Nombre) { return 'token-falso' }
function Read-WAConfirmacion([string]$Frase, [string]$Pregunta) { return $true }
function Get-WAWebhook { return $script:AV.url }
function Send-WAAvisoHttp([string]$Url, $Cuerpo) {
    if ($script:AV.fallar) { return @{ ok = $false; status = 500; incierto = $true } }
    [void]$script:AV.enviados.Add($Cuerpo); return @{ ok = $true; status = 202 }
}
function Invoke-WAZernioGet([string]$Ruta) {
    $script:WA.Contadores.GET++
    if ($Ruta -match '^/inbox/conversations\?') {
        $data = foreach ($k in $script:Z.conv.Keys) {
            $u = ($script:Z.conv[$k].msgs | ForEach-Object { [DateTimeOffset]::Parse($_.createdAt) } | Measure-Object -Property UtcTicks -Maximum).Maximum
            [pscustomobject]@{ id = $k; accountId = $script:CUENTA; platform = 'whatsapp'; updatedTime = ([DateTimeOffset]::new([long]$u, [TimeSpan]::Zero)).ToString('o') }
        }
        $data = @($data | Sort-Object { [DateTimeOffset]::Parse($_.updatedTime) } -Descending)
        return [pscustomobject]@{ data = $data; pagination = [pscustomobject]@{ hasMore = $false }; meta = [pscustomobject]@{ accountsFailed = 0 } }
    }
    if ($Ruta -match '^/inbox/conversations/([^/?]+)/messages\?.*limit=(\d+)') {
        $id = $Matches[1]; $lim = [int]$Matches[2]
        if ($script:Z.alLeer -and $lim -eq 5) { & $script:Z.alLeer; $script:Z.alLeer = $null }
        $ms = @($script:Z.conv[$id].msgs | Sort-Object { [DateTimeOffset]::Parse($_.createdAt) } -Descending | Select-Object -First $lim)
        return [pscustomobject]@{ messages = $ms; pagination = [pscustomobject]@{ hasMore = $false } }
    }
    if ($Ruta -match '^/inbox/conversations/([^/?]+)\?') {
        $id = $Matches[1]
        return [pscustomobject]@{ data = [pscustomobject]@{ id = $id; accountId = $script:CUENTA; platform = 'whatsapp'; isGroup = $false; participantId = $script:Z.conv[$id].tel } }
    }
    throw "Ruta no simulada: $Ruta"
}
function Invoke-WAZernioEnviar([string]$Conversacion, [string]$Texto, [string]$ClaveIdem) {
    $script:WA.Contadores.POST++; $script:Z.posts++
    $modo = $script:Z.fallarPost; $script:Z.fallarPost = $null
    if ($modo -eq 'timeout_sin_envio') { return @{ ok = $false; status = 0; incierto = $true } }
    $m = Add-Msg $Conversacion 'outgoing' $Texto 0 'api' 'cloudapi'
    if ($modo -eq 'timeout_con_envio') { return @{ ok = $false; status = 0; incierto = $true } }
    return @{ ok = $true; status = 200; incierto = $false; data = [pscustomobject]@{ success = $true; data = [pscustomobject]@{ conversationId = $Conversacion; messageId = $m.id } } }
}
function Invoke-WABalter([string]$Fichero, $Cuerpo) {
    if ($Cuerpo.action -eq 'lookup_contact') {
        $script:WA.Contadores.BALTER_LECTURAS++
        $enc = @($script:B.personas | Where-Object {
            ($Cuerpo.email -and $_.email -eq $Cuerpo.email) -or ($Cuerpo.phone -and $_.tel -and ($_.tel -replace '\D', '').EndsWith(($Cuerpo.phone -replace '\D', ''))) })
        $data = @($enc | ForEach-Object { [pscustomobject]@{ person_id = $_.id; name = $_.nombre; roles = @($_.rol) } })
        return @{ ok = $true; status = 200; data = [pscustomobject]@{ status = 'success'; found = ($data.Count -gt 0); matches = $data.Count; data = $data } }
    }
    if ($Cuerpo.action -eq 'search') {
        $arts = @(@($script:B.articulos) | Where-Object { $_ } | ForEach-Object { [pscustomobject]@{ id = 1; name = $_ } })
        return @{ ok = $true; status = 200; data = [pscustomobject]@{ status = 'success'; data = [pscustomobject]@{ articles = $arts } } }
    }
    $script:WA.Contadores.BALTER_ALTAS++
    $modo = $script:B.fallarAlta; $script:B.fallarAlta = $null
    if ($modo -eq 'timeout_sin_alta') { return @{ ok = $false; status = 0; incierto = $true } }
    $script:B.altas++
    $p = [pscustomobject]@{ id = 190000 + $script:B.altas; nombre = $Cuerpo.full_name; email = $Cuerpo.email; tel = $Cuerpo.phone; rol = 'lead' }
    $script:B.personas += $p
    $script:B.ultimaPeticion = $Cuerpo
    if ($modo -eq 'timeout_con_alta') { return @{ ok = $false; status = 0; incierto = $true } }
    return @{ ok = $true; status = 201; data = [pscustomobject]@{ status = 'success'; person_id = $p.id; person_created = $true; chance_id = 12000 + $script:B.altas; chance_created = $true } }
}
function Invoke-WAVigia([string]$Metodo, [string]$Ruta, $Cuerpo) {
    if ($Metodo -eq 'POST') { $script:WA.Contadores.BALTER_ALTAS++ } else { $script:WA.Contadores.BALTER_LECTURAS++ }
    if ($script:V.caido) { return @{ ok = $false; status = 0; incierto = $true } }
    if ($script:V.rutaMala) { return @{ ok = $false; status = 404; incierto = $false; cuerpo_error = '{"error": "Ruta no encontrada"}' } }
    if ($Metodo -eq 'GET' -and $Ruta -match '^/contacts\?(email|phone)=(.+)$') {
        $campo = $Matches[1]; $valor = [Uri]::UnescapeDataString($Matches[2])
        $dig = $valor -replace '\D', ''
        $c = @($script:V.contactos | Where-Object {
            ($campo -eq 'email' -and $_.email -eq $valor.ToLowerInvariant()) -or
            ($campo -eq 'phone' -and $dig -and $_.phone -and ($_.phone -replace '\D', '').EndsWith($dig)) }) | Select-Object -First 1
        if ($c) { return @{ ok = $true; status = 200; incierto = $false; data = $c } }
        return @{ ok = $false; status = 404; incierto = $false; cuerpo_error = '{"error": "Contacto no encontrado"}' }
    }
    if ($Metodo -eq 'POST' -and $Ruta -eq '/enquiries') {
        $script:V.ultima = $Cuerpo
        $modo = $script:V.fallar; $script:V.fallar = $null
        if ($modo -eq 'timeout_sin_alta') { return @{ ok = $false; status = 0; incierto = $true } }
        if ($modo -eq 'rechazo') { return @{ ok = $false; status = 422; incierto = $false; cuerpo_error = '{"error": "Datos no validos"}' } }
        $script:V.altas++
        $c = [pscustomobject]@{ id = 'C-' + $script:V.altas; name = $Cuerpo.name; email = $Cuerpo.email; phone = $Cuerpo.phone }
        $script:V.contactos += $c
        if ($modo -eq 'timeout_con_alta') { return @{ ok = $false; status = 0; incierto = $true } }
        return @{ ok = $true; status = 201; incierto = $false; data = [pscustomobject]@{ contact = $c; opportunity_id = 'OP-' + $script:V.altas; new_contact = $true; new_opportunity = $true; escalated = $false } }
    }
    return @{ ok = $false; status = 404; incierto = $false; cuerpo_error = '{"error": "Ruta no encontrada"}' }
}
function Invoke-WAHermes([string]$Prompt) {
    $script:WA.Contadores.HERMES++; $script:H.llamadas++; $script:H.ultimoPrompt = $Prompt
    if ($script:H.forzar) { $f = $script:H.forzar; $script:H.forzar = $null; return $f }
    $conv = $Prompt.Substring($Prompt.IndexOf('=== CONVERSACION ==='))
    $contacto = (($conv -split "`n") | Where-Object { $_ -match '\] CONTACTO: ' }) -join "`n"
    $email = $null; if ($contacto -match '([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})') { $email = $Matches[1] }
    $nombre = $null; if ($contacto -match 'apellidos son ([A-Za-zÁÉÍÓÚáéíóúñÑ]+ [A-Za-zÁÉÍÓÚáéíóúñÑ]+)' -and $contacto -match 'Soy ([A-Za-zÁÉÍÓÚáéíóúñÑ]+)') {
        $null = $contacto -match 'Soy ([A-Za-zÁÉÍÓÚáéíóúñÑ]+)'; $pn = $Matches[1]; $null = $contacto -match 'apellidos son ([A-Za-zÁÉÍÓÚáéíóúñÑ]+ [A-Za-zÁÉÍÓÚáéíóúñÑ]+)'; $nombre = "$pn $($Matches[1])" }
    $resp = if ($nombre -and $email) { 'Gracias por los datos. Una persona del equipo revisara tu consulta y se pondra en contacto contigo.' }
            else { 'Gracias por escribirnos. Un profesional puede valorar tu consulta. ¿Nos indicas tus apellidos y un correo electronico de contacto?' }
    return ([pscustomobject]@{ respuesta = $resp; idioma = 'es'; nombre_completo = $nombre; email = $email; servicio = 'Compra de local comercial'; resumen = 'Consulta sobre compra de local.'; requiere_humano = $false; motivo_humano = $null } | ConvertTo-Json -Compress)
}

# ------------------------------------------------------------ escenarios
Write-Host "`n1) HTEST: contacto nuevo completa datos en dos turnos" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'piloto_prueba'; New-Conv $script:PRUEBA '34600000107'
Add-Msg $script:PRUEBA 'outgoing' 'Mensaje antiguo de otra prueba' -300 'api' | Out-Null
Add-Msg $script:PRUEBA 'incoming' 'HTEST: Hola, soy Carlos. Necesito asesoramiento para comprar un local comercial en Malaga.' -2 | Out-Null
$r = Ciclo
Check ($r[0].accion -eq 'RESPONDER' -and $script:Z.posts -eq 1) 'Primer mensaje: responde una vez pidiendo los datos que faltan'
Check ((EstadoDe $script:PRUEBA).estado -eq 'CAPTANDO') 'Estado CAPTANDO'
$r = Ciclo
Check ($script:Z.posts -eq 1 -and $script:H.llamadas -eq 1) 'Segundo ciclo sin mensajes nuevos: no vuelve a responder ni llama a Hermes'
Add-Msg $script:PRUEBA 'incoming' 'HTEST: Soy Carlos. Mis apellidos son Vega Romero y mi correo es carlos.prueba1@example.com. Gracias.' | Out-Null
$r = Ciclo
$e = EstadoDe $script:PRUEBA
Check ($script:B.altas -eq 1 -and $e.estado -eq 'ALTA_CREADA' -and $e.opportunity_id -eq 12001) 'Datos completos: crea UNA oportunidad'
Check ($script:Z.posts -eq 2) 'Envia el mensaje de cierre'
Check ($null -eq $script:B.ultimaPeticion.phone -and @($script:B.ultimaPeticion.tags) -contains 'PRUEBA_IA_HERMES') 'En prueba no envia el telefono del probador y etiqueta la oportunidad como prueba'
Check ($script:B.ultimaPeticion.description.Contains('HISTORIAL ORIGINAL INTEGRO') -and $script:B.ultimaPeticion.description.Contains('Vega Romero')) 'La ficha incluye datos estructurados e historial literal'
Add-Msg $script:PRUEBA 'incoming' 'HTEST: Otra cosa mas, gracias.' | Out-Null
$r = Ciclo; $r = Ciclo
Check ($script:B.altas -eq 1 -and $script:Z.posts -eq 2) 'Tras el alta: nuevos mensajes y ciclos repetidos NO generan respuestas ni oportunidades'

Write-Host "`n2) Produccion: el telefono ya existe en BALTER" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c2' '34611111111'
$script:B.personas += [pscustomobject]@{ id = 5; nombre = 'Cliente Antiguo'; email = 'x@x.es'; tel = '+34 611111111'; rol = 'client' }
Add-Msg 'c2' 'incoming' 'Hola, necesito hablar con mi asesora.' -1 | Out-Null
$r = Ciclo
Check ((EstadoDe 'c2').estado -eq 'EXISTENTE' -and $script:Z.posts -eq 0 -and $script:H.llamadas -eq 0) 'Cliente existente: silencio total, ni siquiera se llama a Hermes'
Add-Msg 'c2' 'incoming' 'Hola?' | Out-Null; $r = Ciclo
Check ($script:Z.posts -eq 0 -and $script:WA.Contadores.BALTER_LECTURAS -le 2) 'Siguientes mensajes: sigue en silencio y no vuelve a consultar BALTER'

Write-Host "`n3) Produccion: chat con historial anterior a la puesta en marcha" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c3' '34622222222'
Add-Msg 'c3' 'incoming' 'Mensaje de hace un mes' -43200 | Out-Null
Add-Msg 'c3' 'incoming' 'Hola de nuevo' -1 | Out-Null
$r = Ciclo
Check ((EstadoDe 'c3').estado -eq 'EXISTENTE' -and $script:Z.posts -eq 0) 'Chat antiguo: se trata como contacto existente'

Write-Host "`n4) Produccion: email ya registrado en BALTER" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c4' '34633333333'
$script:B.personas += [pscustomobject]@{ id = 6; nombre = 'Ana Lopez'; email = 'ana@example.com'; tel = $null; rol = 'lead' }
Add-Msg 'c4' 'incoming' 'Hola, soy Ana. Consulta fiscal. Mis apellidos son Lopez Diaz y mi correo es ana@example.com' -1 | Out-Null
$r = Ciclo
Check ((EstadoDe 'c4').estado -eq 'EXISTENTE' -and $script:B.altas -eq 0 -and $script:Z.posts -eq 0) 'Email existente (aunque sea rol lead): no crea ni responde'

Write-Host "`n5) Un profesional escribe en el chat" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c5' '34644444444'
Add-Msg 'c5' 'incoming' 'Hola, soy Pedro, quiero informacion sobre herencias.' -10 | Out-Null
$r = Ciclo
Add-Msg 'c5' 'outgoing' 'Hola Pedro, soy Marina del equipo, te llamo ahora.' -1 $null 'whatsappbusinessapp' | Out-Null
Add-Msg 'c5' 'incoming' 'Perfecto, gracias' | Out-Null
$r = Ciclo
Check ((EstadoDe 'c5').estado -eq 'HUMANO' -and $script:Z.posts -eq 1) 'Relevo humano: el asistente se retira'

Write-Host "`n6) Saludo automatico de WhatsApp Business" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c6' '34655555555'
Add-Msg 'c6' 'incoming' 'Buenas, consulta sobre IVA' -2 | Out-Null
Add-Msg 'c6' 'outgoing' 'Gracias por comunicarte con nosotros. Te responderemos pronto.' -2 $null 'whatsappbusinessapp' | Out-Null
$r = Ciclo
Check ($r[0].accion -eq 'RESPONDER' -and (EstadoDe 'c6').estado -eq 'CAPTANDO') 'El saludo automatico no se confunde con un humano'

Write-Host "`n7) BALTER no responde pero SI crea la oportunidad (timeout)" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c7' '34666666666'
Add-Msg 'c7' 'incoming' 'Hola, soy Luis. Mis apellidos son Mora Gil y mi correo es luis@example.com. Quiero constituir una SL.' -1 | Out-Null
$script:B.fallarAlta = 'timeout_con_alta'
$r = Ciclo
Check ((EstadoDe 'c7').estado -eq 'ALTA_INCIERTA' -and $script:Z.posts -eq 0) 'Resultado incierto: queda ALTA_INCIERTA y no envia nada'
$r = Ciclo
Check ($script:B.altas -eq 1 -and (EstadoDe 'c7').estado -eq 'ALTA_CREADA') 'Siguiente ciclo: comprueba en BALTER, confirma y NO repite el alta'

Write-Host "`n8) BALTER no responde y NO crea (timeout)" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c8' '34677777777'
Add-Msg 'c8' 'incoming' 'Hola, soy Eva. Mis apellidos son Rivas Sanz y mi correo es eva@example.com. Herencia.' -1 | Out-Null
$script:B.fallarAlta = 'timeout_sin_alta'
$r = Ciclo; $r = Ciclo; $r = Ciclo
Check ($script:B.altas -eq 0 -and (EstadoDe 'c8').estado -eq 'REVISION') 'No aparece en BALTER: pasa a revision humana y NO reintenta'

Write-Host "`n9) Zernio no confirma el envio pero el mensaje llego" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c9' '34688888888'
Add-Msg 'c9' 'incoming' 'Hola, consulta sobre alquiler turistico' -1 | Out-Null
$script:Z.fallarPost = 'timeout_con_envio'
$r = Ciclo
Check ((EstadoDe 'c9').estado -eq 'ENVIO_INCIERTO') 'Envio incierto registrado'
$r = Ciclo
$e = EstadoDe 'c9'
Check ($e.estado -eq 'CAPTANDO' -and $script:Z.posts -eq 1 -and $e.respuestas_enviadas -eq 1) 'Siguiente ciclo: lo encuentra en Zernio y NO lo reenvia'

Write-Host "`n10) Zernio no confirma y el mensaje NO llego" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c10' '34699999999'
Add-Msg 'c10' 'incoming' 'Hola, consulta laboral' -1 | Out-Null
$script:Z.fallarPost = 'timeout_sin_envio'
$r = Ciclo; $r = Ciclo; $r = Ciclo
Check ($script:Z.posts -eq 1 -and (EstadoDe 'c10').estado -eq 'REVISION') 'No se reintenta a ciegas: revision humana'

Write-Host "`n11) Llega otro mensaje mientras Hermes redacta" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c11' '34612121212'
Add-Msg 'c11' 'incoming' 'Hola, consulta sobre una compraventa' -1 | Out-Null
$script:Z.alLeer = { Add-Msg 'c11' 'incoming' 'Ah, y es urgente' | Out-Null }
$r = Ciclo
Check ($r[0].accion -eq 'APLAZADA' -and $script:Z.posts -eq 0) 'Se aplaza para responder con todo el contexto'
$r = Ciclo
Check ($script:Z.posts -eq 1) 'En el siguiente ciclo responde una sola vez'

Write-Host "`n12) Hermes inventa datos que el contacto no escribio" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c12' '34613131313'
Add-Msg 'c12' 'incoming' 'Hola, quiero informacion sobre impuestos' -1 | Out-Null
$script:H.forzar = '{"respuesta":"Gracias por escribirnos. ¿Nos indicas tu nombre y un correo?","idioma":"es","nombre_completo":"Juan Perez","email":"juan@example.com","servicio":"Impuestos","resumen":"x","requiere_humano":false}'
$r = Ciclo
$e = EstadoDe 'c12'
Check ($null -eq $e.nombre -and $null -eq $e.email -and $script:B.altas -eq 0) 'Datos no escritos por el contacto: se descartan, no hay alta'

Write-Host "`n13) Mismo email desde otro numero de telefono" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c13a' '34614141414'; New-Conv 'c13b' '34615151515'
Add-Msg 'c13a' 'incoming' 'Hola, soy Sara. Mis apellidos son Gil Paz y mi correo es sara@example.com. Divorcio.' -1 | Out-Null
$r = Ciclo
Add-Msg 'c13b' 'incoming' 'Hola, soy Sara. Mis apellidos son Gil Paz y mi correo es sara@example.com. Os escribo desde otro movil.' | Out-Null
$r = Ciclo
Check ($script:B.altas -eq 1 -and (EstadoDe 'c13b').estado -eq 'EXISTENTE') 'Segunda conversacion con el mismo email: no se duplica'

Write-Host "`n14) Ventana de 24 horas cerrada" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion' @{ inicio_produccion_utc = [DateTimeOffset]::Parse('2026-11-01T00:00:00Z').ToString('o') }; New-Conv 'c14' '34616161616'
Add-Msg 'c14' 'incoming' 'Hola, consulta' -1500 | Out-Null
$r = Ciclo
Check ((EstadoDe 'c14').estado -eq 'REVISION' -and $script:Z.posts -eq 0) 'Fuera de la ventana: no envia, revision humana'

Write-Host "`n15) Limite de respuestas automaticas" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion' @{ max_respuestas_por_conversacion = 2 }; New-Conv 'c15' '34617171717'
Add-Msg 'c15' 'incoming' 'Hola' -1 | Out-Null; $r = Ciclo
Add-Msg 'c15' 'incoming' 'No quiero dar datos' | Out-Null; $r = Ciclo
Add-Msg 'c15' 'incoming' 'Solo informacion' | Out-Null; $r = Ciclo
Check ($script:Z.posts -eq 2 -and (EstadoDe 'c15').estado -eq 'REVISION') 'Tras el limite deja de responder y lo pasa a revision'

Write-Host "`n16) Modo REVISAR no cambia nada" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c16' '34618181818'
Add-Msg 'c16' 'incoming' 'Hola, soy Leo. Mis apellidos son Rey Sol y mi correo es leo@example.com. Sociedad.' -1 | Out-Null
$r = Ciclo $false
Check ($script:Z.posts -eq 0 -and $script:B.altas -eq 0 -and -not (Test-Path (Get-WARutaConv 'c16'))) 'Revisar: sin envios, sin altas y sin guardar estado'

Write-Host "`n17) Nombre con acentos y puntuacion" -ForegroundColor Cyan
Check (Test-WANombreEnTexto 'Lucia Montes' 'HTEST: Buenos dias. Soy Lucía Montes, un nombre ficticio.') 'Lucia Montes == "Lucía Montes,"'
Check (Test-WANombreEnTexto 'Lucía  Montes.' ("Soy Lucía" + [char]0x00A0 + "Montes")) 'Espacio duro y punto final no rompen la comparacion'
Check (-not (Test-WANombreEnTexto 'Lucia Martinez' 'Soy Lucía Montes')) 'Un apellido no escrito se rechaza'
Check (-not (Test-WANombreEnTexto 'Lucia' 'Soy Lucía Montes')) 'Solo el nombre de pila no basta'

Write-Host "`n18) Respuesta de Hermes con email o telefono" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c18' '34619191919'
Add-Msg 'c18' 'incoming' 'Hola, consulta' -1 | Out-Null
$script:H.forzar = '{"respuesta":"Escribenos a info@ejemplo.es o llama al 952 000 000.","idioma":"es","requiere_humano":false}'
$r = Ciclo
Check ($script:Z.posts -eq 0 -and (EstadoDe 'c18').estado -eq 'REVISION') 'No se envia y queda en revision'

Write-Host "`n19) Hermes indica que requiere una persona" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c19' '34620202020'
Add-Msg 'c19' 'incoming' 'Soy cliente vuestro y estoy muy molesto' -1 | Out-Null
$script:H.forzar = '{"respuesta":"Lo trasladamos al equipo.","idioma":"es","requiere_humano":true,"motivo_humano":"Queja de cliente"}'
$r = Ciclo
Check ($script:Z.posts -eq 0 -and (EstadoDe 'c19').estado -eq 'REVISION') 'Silencio y revision humana'

Write-Host "`n20) Dos ciclos a la vez" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'
$job = Start-Job -ScriptBlock { $m = New-Object System.Threading.Mutex($false, 'Local\HACK_Pruebas_Ciclo'); [void]$m.WaitOne(); Start-Sleep 6; $m.ReleaseMutex() }
Start-Sleep 3
$bloqueado = $false
try { $r = Ciclo } catch { $bloqueado = ($_.Exception.Message -match 'YA_HAY_UN_CICLO') }
Check $bloqueado 'Un segundo ciclo simultaneo se detiene sin hacer nada'
$job | Wait-Job | Remove-Job

Write-Host "`n21) HTEST: mensajes de mi movil sin HTEST se ignoran" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'piloto_prueba'; New-Conv $script:PRUEBA '34600000107'
Add-Msg $script:PRUEBA 'incoming' 'Hola, esto es un mensaje personal' -1 | Out-Null
$r = Ciclo
Check ($script:Z.posts -eq 0 -and $script:H.llamadas -eq 0) 'Sin HTEST no se hace nada'

Write-Host "`n22) Produccion: un chat real nuevo y el HTEST en el mismo ciclo" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv $script:PRUEBA '34600000107'; New-Conv 'c22' '34621212121'
Add-Msg $script:PRUEBA 'incoming' 'HTEST: Hola, soy Carlos. Consulta sobre un local.' -1 | Out-Null
Add-Msg 'c22' 'incoming' 'Hola, consulta sobre una herencia' -1 | Out-Null
$r = Ciclo
Check ($script:Z.posts -eq 2 -and (EstadoDe $script:PRUEBA).prueba -eq $true -and (EstadoDe 'c22').prueba -eq $false) 'Atiende los dos y mantiene el HTEST marcado como prueba'

function Get-AvisosNoResumen { return @($script:AV.enviados | Where-Object { $_.titulo -notmatch 'resumen' }) }
Write-Host "`n23) Avisos a Teams" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c23' '34623232323'
Add-Msg 'c23' 'incoming' 'Hola, soy Ines. Mis apellidos son Vela Mar y mi correo es ines@example.com. Herencia.' -1 | Out-Null
$r = Ciclo
Check (@(Get-AvisosNoResumen).Count -eq 1 -and @(Get-AvisosNoResumen)[0].titulo -match 'nueva oportunidad' -and (@(Get-AvisosNoResumen)[0] | ConvertTo-Json -Depth 10) -match 'chance_view/12001') 'Alta creada: un aviso con el enlace a la oportunidad'
$r = Ciclo
Check (@(Get-AvisosNoResumen).Count -eq 1) 'Ciclos siguientes: no repite el aviso'
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c24' '34624242424'
$script:B.personas += [pscustomobject]@{ id = 7; nombre = 'X'; email = 'x@x.es'; tel = '+34624242424'; rol = 'client' }
Add-Msg 'c24' 'incoming' 'Hola' -1 | Out-Null
$r = Ciclo
Check (@(Get-AvisosNoResumen).Count -eq 0) 'Cliente existente: sin aviso (no hace falta)'
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c25' '34625252525'
Add-Msg 'c25' 'incoming' 'Soy cliente y estoy molesto' -1 | Out-Null
$script:H.forzar = '{"respuesta":"x","idioma":"es","requiere_humano":true,"motivo_humano":"Queja de cliente"}'
$script:AV.fallar = $true
$r = Ciclo
Check (@(Get-AvisosNoResumen).Count -eq 0 -and (EstadoDe 'c25').estado -eq 'REVISION') 'Teams no responde: el ciclo sigue y el aviso queda en cola'
$script:AV.fallar = $false
$r = Ciclo
Check (@(Get-AvisosNoResumen).Count -eq 1 -and @(Get-AvisosNoResumen)[0].titulo -match 'revisar') 'Siguiente ciclo: envia el aviso pendiente de revision'
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c26' '34626262626'
Add-Msg 'c26' 'incoming' 'Hola, soy Ivan. Mis apellidos son Paz Gil y mi correo es ivan@example.com. IVA.' -1 | Out-Null
$r = Ciclo $false
Check (@(Get-AvisosNoResumen).Count -eq 0) 'Modo REVISAR: no envia avisos'

Write-Host "`n24) Resumen diario (tambien fines de semana)" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'
$script:Reloj = [DateTimeOffset]::new([datetime]::SpecifyKind([datetime]'2026-11-14T10:00:00','Local'))   # sabado
New-Conv 'c27' '34627272727'
Add-Msg 'c27' 'incoming' 'Hola, soy Olga. Mis apellidos son Rey Luz y mi correo es olga@example.com. Herencia.' -1 | Out-Null
$r = Ciclo
$script:Reloj = [DateTimeOffset]::new([datetime]::SpecifyKind([datetime]'2026-11-15T07:30:00','Local'))
$r = Ciclo
$antes = @($script:AV.enviados | Where-Object { $_.titulo -match 'resumen del 14' }).Count
$script:Reloj = [DateTimeOffset]::new([datetime]::SpecifyKind([datetime]'2026-11-15T08:10:00','Local'))   # domingo
$r = Ciclo; $r = Ciclo
$res = @($script:AV.enviados | Where-Object { $_.titulo -match 'resumen del 14' })
Check ($antes -eq 0 -and $res.Count -eq 1) 'Domingo a partir de las 08:00: un unico resumen del sabado'
Check ($res.Count -eq 1 -and $res[0].texto -match 'Oportunidades creadas en BALTER \(revisa su asignacion\): 1' -and $res[0].texto -match 'Olga Rey Luz' -and $res[0].texto -match 'Mensajes enviados por el asistente: 1') 'El resumen lista la oportunidad (con enlace) y los mensajes enviados'

Write-Host "`n24b) Resumen: cada conversacion cuenta una sola vez" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; $script:WA.Raiz = $script:Raiz
$script:WA.Global = [pscustomobject]@{ envios_por_mes = [pscustomobject]@{} }; $script:WA.Config = [pscustomobject]@{ limite_mensajes_mes = 2000 }
Write-WALog 'cA' 'EXISTENTE' 'x'; Write-WALog 'cA' 'EXISTENTE' 'x'; Write-WALog 'cB' 'EXISTENTE' 'x'; Write-WALog 'cA' 'ENVIO_OK' 'r'; Write-WALog 'cA' 'ENVIO_OK' 'cierre'
$rs = New-WAResumenDia ($script:Reloj.ToLocalTime().DateTime)
Check ($rs.motivo -match 'existentes \(sin responder\): 2' -and $rs.motivo -match 'enviados por el asistente: 2') 'Existentes por conversacion (2) y envios todos (2)'

Write-Host "`n26) Cortes de red: solo se avisa si el fallo persiste" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c28' '34628282828'
$script:Reloj = [DateTimeOffset]::new([datetime]::SpecifyKind([datetime]'2026-11-10T07:00:00','Local'))
$orig = ${function:Invoke-WAZernioGet}
$script:CaerZernio = $true
${function:Invoke-WAZernioGet} = { param([string]$Ruta) if ($script:CaerZernio) { throw 'ZERNIO_GET_FALLO_HTTP_0' }; & $orig $Ruta }
$e1 = $false; try { $r = Ciclo } catch { $e1 = $true }
$script:CaerZernio = $false; $r = Ciclo
Check ($e1 -and @(Get-AvisosNoResumen).Count -eq 0) 'Un corte de un solo ciclo: sin aviso (se recupera solo)'
$script:CaerZernio = $true
foreach ($i in 1..3) { try { $r = Ciclo } catch { } }
Check (@(Get-AvisosNoResumen | Where-Object { $_.titulo -match 'errores' }).Count -eq 0) '3 ciclos (10 minutos) con fallo: aun sin aviso'
try { $r = Ciclo } catch { }
Check (@(Get-AvisosNoResumen | Where-Object { $_.titulo -match 'errores' }).Count -eq 1) '15 minutos con fallo: un aviso de error'
foreach ($i in 1..2) { try { $r = Ciclo } catch { } }
Check (@(Get-AvisosNoResumen | Where-Object { $_.titulo -match 'errores' }).Count -eq 1) 'Mientras sigue caido no repite el aviso'
$script:CaerZernio = $false; $r = Ciclo
Check (@(Get-AvisosNoResumen | Where-Object { $_.titulo -match 'recuperado' }).Count -eq 1) 'Al volver: aviso de recuperacion'
${function:Invoke-WAZernioGet} = $orig

Write-Host "`n27) Intervalo de 1 minuto: el aviso de error espera 15 minutos" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c29' '34629292929'
$script:Reloj = [DateTimeOffset]::new([datetime]::SpecifyKind([datetime]'2026-11-10T06:00:00','Local'))
$script:PasoMin = 1
$orig = ${function:Invoke-WAZernioGet}
$script:CaerZernio = $true
${function:Invoke-WAZernioGet} = { param([string]$Ruta) if ($script:CaerZernio) { throw 'ZERNIO_GET_FALLO_HTTP_0' }; & $orig $Ruta }
foreach ($i in 1..5) { try { $r = Ciclo } catch { } }
Check (@(Get-AvisosNoResumen).Count -eq 0) '5 minutos caido (5 ciclos de 1 min): sin aviso todavia'
$script:CaerZernio = $false; $r = Ciclo
Check (@(Get-AvisosNoResumen).Count -eq 0) 'Se recupera antes de 15 min: ni aviso de error ni de recuperacion'
$script:CaerZernio = $true
foreach ($i in 1..16) { try { $r = Ciclo } catch { } }
Check (@(Get-AvisosNoResumen | Where-Object { $_.titulo -match 'errores' }).Count -eq 1) '16 minutos caido: un aviso de error'
$script:CaerZernio = $false; $r = Ciclo
Check (@(Get-AvisosNoResumen | Where-Object { $_.titulo -match 'recuperado' }).Count -eq 1) 'Al volver: aviso de recuperacion'
${function:Invoke-WAZernioGet} = $orig
$script:PasoMin = 5

Write-Host "`n28) Sin internet: Teams tambien falla; al volver solo llega la recuperacion" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'c30' '34630303030'
$script:Reloj = [DateTimeOffset]::new([datetime]::SpecifyKind([datetime]'2026-11-10T03:00:00','Local'))
$script:PasoMin = 1
$orig = ${function:Invoke-WAZernioGet}
$script:CaerZernio = $true; $script:AV.fallar = $true
${function:Invoke-WAZernioGet} = { param([string]$Ruta) if ($script:CaerZernio) { throw 'ZERNIO_GET_FALLO_HTTP_0' }; & $orig $Ruta }
foreach ($i in 1..20) { try { $r = Ciclo } catch { } }
$script:CaerZernio = $false; $script:AV.fallar = $false; $r = Ciclo
$tits = @(Get-AvisosNoResumen | ForEach-Object { $_.titulo })
Check ($tits.Count -eq 1 -and $tits[0] -match 'recuperado') 'Llega una sola tarjeta (recuperacion), no la de error ya caducada'
${function:Invoke-WAZernioGet} = $orig
$script:PasoMin = 5

Write-Host "`n29) El equipo cierra o devuelve una revision" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'; New-Conv 'cprov00000001e80c6' '34631313131'
Add-Msg 'cprov00000001e80c6' 'incoming' 'Ofrecemos regalos navidenos para empresas' -1 | Out-Null
$script:H.forzar = '{"respuesta":"x","idioma":"es","requiere_humano":true,"motivo_humano":"Proveedor"}'
$r = Ciclo
Check (@(Get-WARevisiones).Count -eq 1) 'La conversacion aparece en la lista de revisiones'
$e = Resolve-WARevision '1e80c6' 'Ignorar' 'proveedor'
Check ($e.estado -eq 'CERRADA' -and @(Get-WARevisiones).Count -eq 0) 'Ignorar: queda CERRADA y sale de la lista'
Add-Msg 'cprov00000001e80c6' 'incoming' 'Le interesa nuestra oferta?' | Out-Null
$r = Ciclo
Check ($script:Z.posts -eq 0 -and (EstadoDe 'cprov00000001e80c6').estado -eq 'CERRADA') 'Aunque insista, el asistente no responde'
$rs = New-WAResumenDia ($script:Reloj.ToLocalTime().DateTime)
Check ($rs.motivo -match 'Revisiones cerradas por el equipo: 1') 'El resumen cuenta la revision cerrada'
Reset-Mundo; Set-Config 'produccion'; New-Conv 'cdudo0000000aa11bb' '34632323232'
Add-Msg 'cdudo0000000aa11bb' 'incoming' 'Hola, soy cliente pero esto es nuevo' -1 | Out-Null
$script:H.forzar = '{"respuesta":"x","idioma":"es","requiere_humano":true,"motivo_humano":"Dice ser cliente"}'
$r = Ciclo
$e = Resolve-WARevision 'aa11bb' 'Retomar' 'es un asunto nuevo'
$r = Ciclo
Check ($e.estado -eq 'CAPTANDO' -and $script:Z.posts -eq 0) 'Retomar: no contesta al mensaje ya revisado'
Add-Msg 'cdudo0000000aa11bb' 'incoming' 'Quiero informacion sobre una compraventa' | Out-Null
$r = Ciclo
Check ($script:Z.posts -eq 1) 'Retomar: responde al siguiente mensaje del contacto'
$err = $null; try { Resolve-WARevision 'zz' 'Ignorar' '' } catch { $err = $_.Exception.Message }
Check ($err -match 'AL_MENOS_4') 'Un ID demasiado corto se rechaza'

Write-Host "`n30) Resumen: chats con movimiento (prueba de que la lectura funciona)" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion'
$script:Reloj = [DateTimeOffset]::new([datetime]::SpecifyKind([datetime]'2026-11-10T10:00:00','Local'))
New-Conv 'cx1' '34633333331'; New-Conv 'cx2' '34633333332'
Add-Msg 'cx1' 'incoming' 'Mensaje de un chat antiguo' -60000 | Out-Null
Add-Msg 'cx1' 'incoming' 'Hola otra vez' -1 | Out-Null
Add-Msg 'cx2' 'incoming' 'Mensaje viejo' -60000 | Out-Null
Add-Msg 'cx2' 'incoming' 'Sigo esperando' -1 | Out-Null
$r = Ciclo; $r = Ciclo
$rs = New-WAResumenDia ($script:Reloj.ToLocalTime().DateTime)
Check ($rs.motivo -match 'Chats de WhatsApp con movimiento \(de cualquier tipo\): 2') 'Cuenta 2 chats con movimiento aunque ambos sean antiguos y sin respuesta'

Write-Host "`n25) Integridad de los scripts" -ForegroundColor Cyan
$ctrl = @(Get-ChildItem $PSScriptRoot -Filter 'HACK-*.ps1' | Where-Object { [IO.File]::ReadAllText($_.FullName) -match '[\x00-\x08\x0B\x0C\x0E-\x1F]' })
Check ($ctrl.Count -eq 0) 'Ningun script contiene caracteres de control (rutas de Windows correctas)'
Check ((Get-WARutaWebhook) -match 'HACK-WhatsApp[\\/]claves[\\/]aviso-teams\.dpapi$') 'Ruta del aviso de Teams correcta'

Write-Host "`n31) Hackathon: HTEST se detecta solo y crea UNA ficha de prueba" -ForegroundColor Cyan
$demo = @{ prefijo_prueba = 'HTEST'; deteccion_prueba_automatica = $true; etiqueta = 'Asistente Virtual Vigía:'
    etiquetas_extra = @('DEMO', 'Vigia'); mutex = 'Local\HACK_Pruebas_Ciclo'; perfil_hermes = 'hackaton-demo'
    empresa = [pscustomobject]@{ nombre = 'Vigía'; actividad = 'Agentes de IA para pymes.'; quien_contacta = 'una persona del equipo de Vigía'
        aviso_primer_mensaje = 'Soy un asistente virtual de demostracion.' } }
Reset-Mundo; Set-Config 'produccion' $demo; New-Conv 'ht1' '34611111111'
Add-Msg 'ht1' 'incoming' 'HTEST: Hola, soy Carlos. Quiero una demo de Vigia.' -1 | Out-Null
$r = Ciclo
$e = EstadoDe 'ht1'
Check ($r[0].accion -eq 'RESPONDER' -and $script:Z.posts -eq 1 -and $e.prueba -eq $true) 'Un chat con HTEST es prueba sin estar en conversaciones_prueba'
$ult = @($script:Z.conv['ht1'].msgs)[-1]
Check (([string]$ult.message).Contains('Asistente Virtual Vigía:') -and -not ([string]$ult.message).Contains('Asistente Virtual:')) 'Responde con la etiqueta de la demo'
Check ($script:H.ultimoPrompt.Contains('Vigía') -and $script:H.ultimoPrompt.Contains('WHATSAPP DE Vigía') -and $script:H.ultimoPrompt.Contains('asistente virtual de demostracion')) 'El prompt es el de la empresa de la demo, con el aviso del primer mensaje'
Check ($script:H.ultimoPrompt.Contains('CONTACTO: Hola, soy Carlos')) 'Quita el prefijo HTEST antes de pasar el texto a Hermes'
Add-Msg 'ht1' 'incoming' 'Soy Carlos. Mis apellidos son Vega Romero y mi correo es carlos.htest@example.com.' | Out-Null
$r = Ciclo
$e = EstadoDe 'ht1'
Check ($script:B.altas -eq 1 -and $e.estado -eq 'ALTA_CREADA') 'Segundo mensaje sin prefijo: sigue siendo prueba y crea UNA oportunidad'
Check (@($script:B.ultimaPeticion.tags) -contains 'DEMO' -and @($script:B.ultimaPeticion.tags) -contains 'PRUEBA_IA_HERMES' -and $null -eq $script:B.ultimaPeticion.phone) 'Ficha etiquetada DEMO y PRUEBA, sin el telefono del probador'
$r = Ciclo; $r = Ciclo
Check ($script:B.altas -eq 1) 'Mas ciclos: no duplica la oportunidad'

Write-Host "`n32) Hackathon: un chat sin HTEST es un contacto real de la demo" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion' $demo; New-Conv 'pub1' '34622222222'
Add-Msg 'pub1' 'incoming' 'Hola, quiero informacion de Vigia' -1 | Out-Null
$r = Ciclo
$e = EstadoDe 'pub1'
Check ($r[0].accion -eq 'RESPONDER' -and $e.prueba -ne $true) 'Contacto del publico: se atiende como real'
Check ($script:B.altas -eq 0 -and $script:WA.Contadores.BALTER_LECTURAS -ge 1) 'Comprueba su telefono en el ERP antes de responder'

Write-Host "`n33) Hackathon: valores de la instancia" -ForegroundColor Cyan
Check ($script:WAInstancia.mutex -eq 'Local\HACK_Pruebas_Ciclo' -and $script:WAInstancia.perfil_hermes -eq 'hackaton-demo') 'Usa el mutex y el perfil de Hermes de la config, no los de produccion'
Check ((Format-WAMensajeAsistente 'Gracias por escribirnos, en breve te atendemos.').StartsWith([char]::ConvertFromUtf32(0x1F916) + ' Asistente Virtual Vigía:')) 'El prefijo del bot sale de la config'
$err = $null; try { Format-WAMensajeAsistente 'Asistente Virtual Vigía: Gracias por escribirnos, en breve te atendemos.' | Out-Null } catch { $err = $_.Exception.Message }
Check ($err -eq $null) 'Un prefijo repetido por Hermes se limpia'

Write-Host "`n34) Hackathon: -NuevaPrueba permite otra ficha desde el mismo movil" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion' $demo; New-Conv 'ht2' '34633333333'
Add-Msg 'ht2' 'incoming' 'HTEST: Hola, soy Carlos. Quiero una demo.' -1 | Out-Null
$r = Ciclo
Add-Msg 'ht2' 'incoming' 'Soy Carlos. Mis apellidos son Vega Romero y mi correo es carlos.htest@example.com.' | Out-Null
$r = Ciclo
Check ($script:B.altas -eq 1 -and (EstadoDe 'ht2').estado -eq 'ALTA_CREADA') 'Primera ficha creada'
$script:Reloj = $script:Reloj.AddMinutes(1)
$n = Reset-WAPruebas $script:Raiz
Check ($n -ge 1 -and (EstadoDe 'ht2').estado -eq 'NUEVA') 'Nueva sesion: archiva la conversacion de prueba'
$script:Reloj = $script:Reloj.AddMinutes(1)
Add-Msg 'ht2' 'incoming' 'HTEST: Hola otra vez, soy Lucia. Quiero informacion.' | Out-Null
$r = Ciclo
Check ($r[0].accion -eq 'RESPONDER' -and -not $script:H.ultimoPrompt.Contains('carlos.htest@example.com')) 'Solo lee lo escrito desde la nueva sesion'
Add-Msg 'ht2' 'incoming' 'Soy Lucia. Mis apellidos son Gil Mora y mi correo es lucia.htest@example.com.' | Out-Null
$r = Ciclo
Check ($script:B.altas -eq 2 -and $script:B.ultimaPeticion.full_name -eq 'Lucia Gil Mora') 'Segunda ficha, con los datos nuevos'
$r = Ciclo
Check ($script:B.altas -eq 2) 'Sin duplicados despues'

Write-Host "`n35) Hackathon: companero cuyo telefono ya esta en el ERP como empleado" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion' $demo; New-Conv 'emp1' '34644444444'
$script:B.personas += [pscustomobject]@{ id = 777; nombre = 'Empleado Demo'; email = 'empleado@demo.es'; tel = '+34 644 444 444'; rol = 'contact' }
Add-Msg 'emp1' 'incoming' 'Hola, probando' -1 | Out-Null
$r = Ciclo
Check ((EstadoDe 'emp1').estado -eq 'EXISTENTE' -and $script:Z.posts -eq 0) 'Sin HTEST: su telefono ya esta en el ERP, no se le responde'
$script:Reloj = $script:Reloj.AddMinutes(1)
$n = Reset-WAPruebas $script:Raiz
$script:Reloj = $script:Reloj.AddMinutes(1)
Add-Msg 'emp1' 'incoming' 'HTEST: Hola, soy Marta. Quiero una demo.' | Out-Null
$r = Ciclo
Check ($n -ge 1 -and $r[0].accion -eq 'RESPONDER' -and (EstadoDe 'emp1').prueba -eq $true) 'Tras -NuevaPrueba, con HTEST se le atiende como prueba'
Add-Msg 'emp1' 'incoming' 'Soy Marta. Mis apellidos son Rivas Sol y mi correo es marta.htest@example.com.' | Out-Null
$r = Ciclo
Check ($script:B.altas -eq 1 -and $null -eq $script:B.ultimaPeticion.phone -and $null -eq $script:B.ultimaPeticion.person_id) 'Crea una ficha NUEVA sin su telefono de empleado'

Write-Host "`n36) Hackathon: clave de BALTER de otra empresa" -ForegroundColor Cyan
$demoControl = @{}; foreach ($k in $demo.Keys) { $demoControl[$k] = $demo[$k] }; $demoControl['balter_control_articulo'] = 'Producto control demo'
Reset-Mundo; Set-Config 'produccion' $demoControl; New-Conv 'ht9' '34655555555'
Add-Msg 'ht9' 'incoming' 'HTEST: Soy Pepe. Mis apellidos son Paz Gil y mi correo es pepe.htest@example.com.' -1 | Out-Null
$script:WAEmpresaVerificada = $null
$err = $null; try { $r = Ciclo } catch { $err = $_.Exception.Message }
Check ($err -eq 'CLAVE_BALTER_NO_ES_DE_LA_EMPRESA_DE_LA_DEMO' -and $script:B.altas -eq 0 -and $script:Z.posts -eq 0 -and $script:H.llamadas -eq 0) 'Si el catalogo no tiene el articulo de control: el ciclo se para sin leer, responder ni crear nada'
$script:B.articulos = @('Producto control demo')
$err = $null; try { $r = Ciclo } catch { $err = $_.Exception.Message }
Check ($null -eq $err -and $r[0].accion -eq 'CREAR_OPORTUNIDAD_Y_CERRAR' -and $script:B.altas -eq 1) 'Con el articulo de control en el catalogo: funciona (crea la ficha)'

Write-Host "`n37) Destino por defecto: ERP de demo de Vigia. HTEST crea UNA consulta" -ForegroundColor Cyan
$vig = @{}; foreach ($k in $demo.Keys) { $vig[$k] = $demo[$k] }
$vig['erp'] = [pscustomobject]@{ tipo = 'vigia'; url = 'http://127.0.0.1:8765/api/v1' }; $vig['balter_control_articulo'] = ''; $vig['balter_autorizado_por'] = ''
Reset-Mundo; Set-Config 'produccion' $vig; New-Conv 'v1' '34611111111'
Add-Msg 'v1' 'incoming' 'HTEST: Hola, soy Carlos. Quiero una demo de Vigia.' -1 | Out-Null
$r = Ciclo
Check ($r[0].accion -eq 'RESPONDER' -and $script:B.altas -eq 0 -and $script:WA.Contadores.BALTER_LECTURAS -ge 1) 'Comprueba el ERP de Vigia antes de nada y no toca BALTER'
Add-Msg 'v1' 'incoming' 'Soy Carlos. Mis apellidos son Vega Romero y mi correo es carlos.htest@example.com.' | Out-Null
$r = Ciclo
$e = EstadoDe 'v1'; $u = $script:V.ultima
Check ($script:V.altas -eq 1 -and $script:B.altas -eq 0 -and $e.estado -eq 'ALTA_CREADA' -and $e.opportunity_id -eq 'OP-1') 'Crea UNA consulta en el ERP de Vigia (OP-1) y ninguna en BALTER'
Check ($u.name -eq 'Carlos Vega Romero' -and $u.email -eq 'carlos.htest@example.com' -and $null -eq $u.phone -and $u.channel -eq 'whatsapp') 'Nombre y correo validados, canal WhatsApp y sin el telefono del probador'
Check ($u.summary.StartsWith('PRUEBA (HTEST)') -and $u.topic -eq 'Compra de local comercial' -and $u.summary.Length -le 2000) 'Resumen marcado como prueba, asunto de Hermes y dentro del limite del ERP'
Check ((ConvertTo-WAFecha $u.answered_at) -ge (ConvertTo-WAFecha $u.received_at)) 'Hora de respuesta posterior a la de llegada (el agente de captacion mide ese tiempo)'
Check (-not ([string]$u.summary).Contains('Mis apellidos son')) 'Minimo necesario: no copia la conversacion al ERP'
$r = Ciclo; $r = Ciclo
Check ($script:V.altas -eq 1 -and $script:Z.posts -eq 2) 'Mas ciclos: ni otra consulta ni otro mensaje'

Write-Host "`n38) Vigia: contacto del publico ya registrado en el ERP" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion' $vig; New-Conv 'v2' '34622222222'
$script:V.contactos += [pscustomobject]@{ id = 'C-9'; name = 'Cliente Demo'; email = 'cliente@demo.es'; phone = '+34622222222' }
Add-Msg 'v2' 'incoming' 'Hola, quiero informacion' -1 | Out-Null
$r = Ciclo
Check ((EstadoDe 'v2').estado -eq 'EXISTENTE' -and $script:Z.posts -eq 0 -and $script:V.altas -eq 0) 'Su telefono ya esta en el ERP: no responde ni crea nada'

Write-Host "`n39) Vigia: contacto real nuevo, con su telefono" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion' $vig; New-Conv 'v3' '34633333333'
Add-Msg 'v3' 'incoming' 'Hola, soy Lucia. Mis apellidos son Gil Mora y mi correo es lucia.demo@example.com.' -1 | Out-Null
$r = Ciclo
Check ($script:V.altas -eq 1 -and $script:V.ultima.phone -eq '+34633333333' -and -not $script:V.ultima.summary.StartsWith('PRUEBA')) 'Crea la consulta con el telefono verificado por WhatsApp'

Write-Host "`n40) Vigia: ERP caido o mal configurado" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion' $vig; New-Conv 'v4' '34644444444'
Add-Msg 'v4' 'incoming' 'HTEST: Soy Pepe. Mis apellidos son Paz Gil y mi correo es pepe.htest@example.com.' -1 | Out-Null
$script:V.caido = $true
$err = $null; try { $r = Ciclo } catch { $err = $_.Exception.Message }
Check ($err -match '^ERP_DE_VIGIA_NO_DISPONIBLE' -and $script:Z.posts -eq 0 -and $script:H.llamadas -eq 0) 'ERP sin respuesta: el ciclo se para sin leer, responder ni llamar a Hermes'
$script:V.caido = $false; $script:V.rutaMala = $true
$err = $null; try { $r = Ciclo } catch { $err = $_.Exception.Message }
Check ($err -match '^ERP_DE_VIGIA_NO_DISPONIBLE_HTTP_404' -and $script:V.altas -eq 0) 'URL mal escrita (404 de ruta, no de contacto): se para, no lo toma por no existe'
$script:V.rutaMala = $false
$err = $null; try { $r = Ciclo } catch { $err = $_.Exception.Message }
Check ($null -eq $err -and $script:V.altas -eq 1) 'Con el ERP disponible: funciona'

Write-Host "`n41) Vigia: alta sin respuesta del ERP" -ForegroundColor Cyan
Reset-Mundo; Set-Config 'produccion' $vig; New-Conv 'v5' '34655555555'
Add-Msg 'v5' 'incoming' 'HTEST: Soy Ana. Mis apellidos son Rey Sol y mi correo es ana.htest@example.com.' -1 | Out-Null
$script:V.fallar = 'timeout_con_alta'
$r = Ciclo
Check ((EstadoDe 'v5').estado -eq 'ALTA_INCIERTA' -and $script:Z.posts -eq 0) 'Timeout: queda incierta y no envia el cierre'
$r = Ciclo
Check ((EstadoDe 'v5').estado -eq 'ALTA_CREADA' -and $script:V.altas -eq 1) 'Siguiente ciclo: la encuentra por correo y NO repite el alta'
Reset-Mundo; Set-Config 'produccion' $vig; New-Conv 'v6' '34666666666'
Add-Msg 'v6' 'incoming' 'HTEST: Soy Eva. Mis apellidos son Luz Mar y mi correo es eva.htest@example.com.' -1 | Out-Null
$script:V.fallar = 'rechazo'
$r = Ciclo
Check ((EstadoDe 'v6').estado -eq 'REVISION' -and $script:V.altas -eq 0 -and $script:Z.posts -eq 0) 'El ERP rechaza los datos (422): revision humana, sin reintentos'

Write-Host "`n42) BALTER solo con permiso por escrito; URL insegura" -ForegroundColor Cyan
$sinPermiso = @{}; foreach ($k in $demo.Keys) { $sinPermiso[$k] = $demo[$k] }; $sinPermiso['balter_autorizado_por'] = ''
Reset-Mundo; Set-Config 'produccion' $sinPermiso; New-Conv 'b1' '34677777777'
Add-Msg 'b1' 'incoming' 'HTEST: Soy Leo. Mis apellidos son Mar Sol y mi correo es leo.htest@example.com.' -1 | Out-Null
$err = $null; try { $r = Ciclo } catch { $err = $_.Exception.Message }
Check ($err -eq 'BALTER_SIN_PERMISO_POR_ESCRITO' -and $script:B.altas -eq 0 -and $script:WA.Contadores.BALTER_LECTURAS -eq 0 -and $script:Z.posts -eq 0) 'Sin quien autorizo por escrito: no lee, no responde y no crea nada en BALTER'
$insegura = @{}; foreach ($k in $vig.Keys) { $insegura[$k] = $vig[$k] }; $insegura['erp'] = [pscustomobject]@{ tipo = 'vigia'; url = 'http://erp.example.com/api/v1' }
Reset-Mundo; Set-Config 'produccion' $insegura; New-Conv 'b2' '34688888888'
Add-Msg 'b2' 'incoming' 'HTEST: Hola' -1 | Out-Null
$err = $null; try { $r = Ciclo } catch { $err = $_.Exception.Message }
Check ($err -eq 'URL_DEL_ERP_DE_VIGIA_NO_PERMITIDA' -and $script:WA.Contadores.BALTER_LECTURAS -eq 0) 'HTTP sin cifrar fuera de la red local: no envia el token'
Check ((Test-WAUrlErpSegura 'http://192.168.1.20:8765/api/v1') -and (Test-WAUrlErpSegura 'https://erp.example.com/api/v1') -and -not (Test-WAUrlErpSegura 'ftp://127.0.0.1/x')) 'Red local por HTTP y cualquier sitio por HTTPS'

Write-Host "`n43) Validacion de los datos que extrae Hermes" -ForegroundColor Cyan
Check (Test-WAEmailEnTexto 'Ana@Example.com' 'mi correo es ana@example.com, gracias') 'Correo exacto (sin importar mayusculas): valido'
Check (-not (Test-WAEmailEnTexto 'ana@gmail.co' 'mi correo es ana@gmail.com')) 'Correo recortado: NO valido'
Check (-not (Test-WAEmailEnTexto 'a@b.co' 'escribeme a xa@b.co')) 'Correo contenido en otro: NO valido'
Check (Test-WANombreEnTexto 'Ana López García' 'Hola, soy ana lopez garcia.') 'Nombre escrito tal cual: valido'
Check (Test-WANombreEnTexto 'Carlos Vega Romero' "Soy Carlos.`nMis apellidos son Vega Romero") 'Nombre y apellidos en mensajes distintos: valido'
Check (-not (Test-WANombreEnTexto 'Ana Ruiz' 'soy Ana, quiero informacion')) 'Un apellido que el contacto no escribio: NO valido'
$err = $null; try { Format-WAMensajeAsistente 'Gracias. Completa tu alta en https://pago.example.com hoy mismo.' | Out-Null } catch { $err = $_.Exception.Message }
Check ($err -eq 'RESPUESTA_CON_ENLACE') 'Respuesta con un enlace: no se envia'
$err = $null; try { Format-WAMensajeAsistente 'Gracias. Visita www.ejemplo.es para mas informacion.' | Out-Null } catch { $err = $_.Exception.Message }
Check ($err -eq 'RESPUESTA_CON_ENLACE') 'Respuesta con www: no se envia'

Write-Host ''
Write-Host ("RESULTADO: {0} comprobaciones correctas, {1} fallos" -f $script:T.ok, $script:T.fallos.Count) -ForegroundColor $(if ($script:T.fallos.Count -eq 0) { 'Green' } else { 'Red' })
foreach ($f in $script:T.fallos) { Write-Host " - $f" -ForegroundColor Red }
if ($script:T.fallos.Count -gt 0) { exit 1 }

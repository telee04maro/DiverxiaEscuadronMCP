<#
  Asistente de WhatsApp del hackathon (instancia de demostracion, separada de cualquier instalacion de produccion)
  Zernio -> Hermes (perfil hackaton-demo) -> ERP de demo de Vigia (por defecto; BALTER solo con permiso, ADR 008)
  Nuevo: -ActivarFondo [-Segundos N]  el asistente funciona SOLO, oculto, cada N segundos (5 a 60), sin depender de
         ninguna ventana. Si se cae, el Programador de tareas lo relanza en 1 minuto. -Parar lo detiene.
         -Monitor   muestra en directo lo que hace (cerrar esta ventana NO lo para).
         -Bucle [-Segundos N]  lo mismo pero en esta ventana (solo para pruebas).

  Uso (desde PowerShell, en cualquier carpeta):
    & "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -NuevaPrueba
    & "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1"            # REVISAR: lee y redacta, no envia ni crea
    & "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -Ejecutar  # pide ENVIAR / CREAR antes de cada accion
    & "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -Estado    # muestra el estado de cada conversacion
    & "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -Reabrir   # devuelve a CAPTANDO una prueba en REVISION
    & "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -ActivarProduccion  # empieza a leer chats reales nuevos (sin envios automaticos)
    & "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -ConfigurarAviso    # guarda cifrada la URL del flujo de Teams
    & "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -ProbarAviso        # envia un aviso de prueba a Teams
    & "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -ActivarAutomatico  # ciclo solo cada 5 minutos (o -ActivarAutomatico -Minutos 1)
    & "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -ActivarAutomatico -SinSesion  # tambien sin iniciar sesion (pide tu contrasena de Windows)
    & "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -Parar              # PARADA INMEDIATA del automatico
    & "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -ResumenHoy         # envia a Teams el resumen de hoy
    & "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -Revisiones         # lista las conversaciones pendientes de revision
    & "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -Ignorar 1e80c6 -Nota "proveedor"   # cierra una revision
    & "$env:LOCALAPPDATA\HACK-WhatsApp\ciclo\HACK-Ciclo.ps1" -Retomar 1e80c6     # la devuelve al asistente
#>
param(
    [switch]$Ejecutar,
    [switch]$Automatico,
    [switch]$NuevaPrueba,
    [switch]$Estado,
    [switch]$Reabrir,
    [switch]$ActivarProduccion,
    [switch]$ConfigurarAviso,
    [switch]$ProbarAviso,
    [switch]$ActivarAutomatico,
    [switch]$Parar,
    [switch]$ResumenHoy,
    [ValidateRange(1, 60)][int]$Minutos = 0,
    [switch]$Revisiones,
    [string]$Ignorar,
    [string]$Retomar,
    [string]$Nota,
    [switch]$SinSesion,
    [switch]$Bucle,
    [switch]$Oculto,
    [switch]$ActivarFondo,
    [switch]$Monitor,
    [ValidateRange(0, 60)][int]$Segundos = 0
)
$tarea = 'HACK WhatsApp - Demo'
$ErrorActionPreference = 'Stop'
$raiz = $PSScriptRoot
. (Join-Path $raiz 'HACK-Ciclo-Lib.ps1')
$script:WA.Raiz = $raiz

# Barreras: config.json de la demo (local, fuera del repositorio) puede listar en "proteger" la instalacion
# de produccion de este equipo (carpeta, mutex, perfil de Hermes). Si coincide, el script se para.
$cfgInstancia = Read-WAJson (Join-Path $raiz 'config.json')
if ($null -eq $cfgInstancia) { Write-Host 'Falta config.json: ejecuta antes HACK-Instalar.ps1.' -ForegroundColor Red; return }
$proteger = Get-WAProp $cfgInstancia 'proteger' $null
foreach ($carpeta in @(Get-WAProp $proteger 'carpeta_ciclo' @())) {
    if (-not $carpeta) { continue }
    $prod = Join-Path $env:LOCALAPPDATA $carpeta
    if ($raiz.TrimEnd('\').ToLowerInvariant().StartsWith($prod.TrimEnd('\').ToLowerInvariant())) {
        Write-Host 'PARADO: este script no puede ejecutarse dentro de la carpeta de produccion protegida.' -ForegroundColor Red; return
    }
}
if ([string]::IsNullOrWhiteSpace([string](Get-WAProp $cfgInstancia 'carpeta_claves' '')) -or
    @(Get-WAProp $proteger 'mutex' @()) -contains [string](Get-WAProp $cfgInstancia 'mutex' '') -or
    @(Get-WAProp $proteger 'perfil_hermes' @()) -contains [string](Get-WAProp $cfgInstancia 'perfil_hermes' '') -or
    (-not ($Parar -or $Estado -or $Monitor -or $Revisiones) -and
     ([string](Get-WAProp (Get-WAProp $cfgInstancia 'erp' $null) 'tipo' 'vigia')).ToLowerInvariant() -eq 'balter' -and
     ([string]::IsNullOrWhiteSpace([string](Get-WAProp $cfgInstancia 'balter_control_articulo' '')) -or
      [string]::IsNullOrWhiteSpace([string](Get-WAProp $cfgInstancia 'balter_autorizado_por' ''))))) {
    Write-Host 'PARADO: config.json no tiene los valores propios de la demo (claves, mutex, perfil de Hermes o, con BALTER, el articulo de control y quien autorizo por escrito). Revisa HACK-Instalar.ps1.' -ForegroundColor Red; return
}
Set-WAInstancia $cfgInstancia

if ($NuevaPrueba) {
    # Archiva (no borra) todas las conversaciones de prueba y empieza una sesion nueva:
    # cada movil puede volver a escribir HTEST y crear OTRA ficha. Se puede usar con el -Bucle en marcha.
    $n = Reset-WAPruebas $raiz
    Write-Host "Nueva sesion de pruebas preparada ($n conversacion(es) de prueba archivadas; no se borra nada)." -ForegroundColor Green
    Write-Host ('Ahora escribe desde el movil un WhatsApp que empiece por ' + $script:WAInstancia.prefijo_prueba + ': con datos ficticios.')
    Write-Host 'Usa un nombre y un correo ficticios NUEVOS cada vez (por ejemplo ana.lopez.htest2@example.com).'
    return
}
if ($Parar) {
    $cfgPath = Join-Path $raiz 'config.json'
    $cfg = Read-WAJson $cfgPath
    $cfg.automatico_habilitado = $false
    Write-WAJson $cfgPath $cfg
    $t = Get-ScheduledTask -TaskName $tarea -ErrorAction SilentlyContinue
    if ($t) { Disable-ScheduledTask -TaskName $tarea | Out-Null }
    Write-WALog '-' 'AUTOMATICO_PARADO' 'Parada manual'
    Write-Host 'PARADO: el asistente ya no actua solo. Puedes seguir usando -Ejecutar a mano.' -ForegroundColor Yellow
    return
}

if ($ConfigurarAviso) {
    Write-Host 'Pega la URL del flujo de Teams (no se mostrara en pantalla) y pulsa Intro.'
    $seguro = Read-Host 'URL del flujo' -AsSecureString
    $plano = (New-Object System.Net.NetworkCredential('', $seguro)).Password
    if (-not $plano.StartsWith('https://')) { Write-Host 'La URL no empieza por https://. No se ha guardado nada.' -ForegroundColor Red; return }
    $plano = $null
    $dir = Split-Path (Get-WARutaWebhook) -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Set-Content -LiteralPath (Get-WARutaWebhook) -Value (ConvertFrom-SecureString $seguro) -Encoding UTF8
    Write-Host 'URL guardada cifrada en este usuario de Windows. Ahora ejecuta -ProbarAviso.' -ForegroundColor Green
    return
}

if ($ResumenHoy) {
    # Envia a Teams el resumen de lo que va de hoy (para comprobar el formato).
    $script:WA.Config = Read-WAJson (Join-Path $raiz 'config.json')
    $script:WA.Global = Read-WAJson (Join-Path $raiz 'estado\global.json')
    if ($null -eq $script:WA.Global) { $script:WA.Global = [pscustomobject]@{ envios_por_mes = [pscustomobject]@{} } }
    $res = New-WAResumenDia (Get-Date)
    Write-Host $res.motivo
    $url = Get-WAWebhook
    if ($null -eq $url) { Write-Host 'Sin aviso de Teams configurado: solo se muestra en pantalla.'; return }
    $r = Send-WAAvisoHttp $url (New-WATarjetaAviso $res)
    Write-Host $(if ($r.ok) { 'Resumen enviado a Teams.' } else { "No se pudo enviar (HTTP $($r.status))." })
    return
}

if ($ProbarAviso) {
    $url = Get-WAWebhook
    if ($null -eq $url) { Write-Host 'Primero ejecuta -ConfigurarAviso.' -ForegroundColor Red; return }
    $r = Send-WAAvisoHttp $url (New-WATarjetaAviso ([pscustomobject]@{ tipo = 'PRUEBA'; motivo = 'Comprobacion de la conexion con Teams'; nombre = 'Contacto ficticio'; servicio = 'Prueba del aviso' }))
    if ($r.ok) { Write-Host "Aviso enviado (HTTP $($r.status)). Comprueba que aparece en Teams." -ForegroundColor Green }
    else { Write-Host "El aviso no se pudo enviar (HTTP $($r.status)). Revisa la URL del flujo." -ForegroundColor Red }
    return
}

if ($Monitor) {
    # Solo mira el registro: cerrar esta ventana no afecta al asistente.
    $f = Join-Path $raiz ('registro\bucle-' + (Get-Date).ToString('yyyy-MM-dd') + '.txt')
    $cfg = Read-WAJson (Join-Path $raiz 'config.json')
    Clear-Host
    Write-Host '=== ASISTENTE WHATSAPP (HACKATHON) - MONITOR ===' -ForegroundColor Cyan
    Write-Host ('Automatico: ' + $(if ($cfg.automatico_habilitado -eq $true) { 'ACTIVADO' } else { 'PARADO' }))
    $t = Get-ScheduledTask -TaskName $tarea -ErrorAction SilentlyContinue
    if ($t) { Write-Host ('Tarea programada: ' + $t.State) } else { Write-Host 'Tarea programada: no existe (usa -ActivarFondo)' }
    Write-Host 'Cerrar esta ventana NO para el asistente. Para pararlo: -Parar' -ForegroundColor Yellow
    Write-Host ''
    if (-not (Test-Path -LiteralPath $f)) { Write-Host 'Todavia no hay registro de hoy: esperando...'; while (-not (Test-Path -LiteralPath $f)) { Start-Sleep -Seconds 2 } }
    Get-Content -LiteralPath $f -Tail 40 -Wait -Encoding UTF8
    return
}
if ($ActivarFondo) {
    $cfgPath = Join-Path $raiz 'config.json'
    $cfg = Read-WAJson $cfgPath
    if ($cfg.modo -ne 'produccion') { Write-Host 'Primero activa la produccion (-ActivarProduccion).' -ForegroundColor Red; return }
    $seg = $Segundos
    if ($seg -eq 0) { $seg = [int](Get-WAProp $cfg 'intervalo_segundos' 10) }
    if ($seg -lt 5) { $seg = 5 }  # menos de 5 s castiga a Zernio sin mejorar la demo
    $vbs = Join-Path $raiz 'HACK-Bucle-Oculto.vbs'
    if (-not (Test-Path -LiteralPath $vbs)) { Write-Host 'Falta HACK-Bucle-Oculto.vbs: vuelve a ejecutar HACK-Instalar.ps1.' -ForegroundColor Red; return }
    Write-Host "El asistente funcionara SOLO y OCULTO: revisa el WhatsApp cada $seg segundos, responde y crea oportunidades."
    Write-Host 'No depende de ninguna ventana. Si se detiene por un error, Windows lo relanza en 1 minuto.'
    Write-Host 'Funciona mientras tu sesion de Windows este iniciada (aunque la pantalla este bloqueada).'
    Write-Host 'Para verlo: -Monitor     Para pararlo: -Parar'
    if (-not (Read-WAConfirmacion 'AUTOMATICO' 'Escribe AUTOMATICO para activarlo (cualquier otra cosa = no)')) { Write-Host 'Cancelado.'; return }
    $quien = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    $accion = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument ('//B //Nologo "' + $vbs + '"')
    # Cada minuto el Programador comprueba que el bucle sigue vivo (IgnoreNew: si ya corre, no hace nada).
    $disparo = @(
        (New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(15) -RepetitionInterval (New-TimeSpan -Minutes 1)),
        (New-ScheduledTaskTrigger -AtLogOn -User $quien)
    )
    $ajustes = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    $usuario = New-ScheduledTaskPrincipal -UserId $quien -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $tarea -Action $accion -Trigger $disparo -Settings $ajustes -Principal $usuario -Force | Out-Null
    Enable-ScheduledTask -TaskName $tarea | Out-Null
    $cfg.automatico_habilitado = $true
    Set-WAProp $cfg 'intervalo_segundos' $seg
    Write-WAJson $cfgPath $cfg
    Write-WALog '-' 'FONDO_ACTIVADO' "Cada $seg segundos (tarea $tarea)"
    Write-Host "ACTIVADO. Empieza en unos 15 segundos. Tarea programada: '$tarea'." -ForegroundColor Green
    Write-Host 'Consejo: desactiva la suspension del equipo mientras dure la demo:  powercfg /change standby-timeout-ac 0'
    return
}
if ($Bucle) {
    # Bucle de revision cada pocos segundos. Visible (pruebas) u -Oculto (lo lanza la tarea programada).
    $cfgPath = Join-Path $raiz 'config.json'
    $cfg = Read-WAJson $cfgPath
    if ($cfg.modo -ne 'produccion') { Write-Host 'Primero activa la produccion (-ActivarProduccion).' -ForegroundColor Red; return }
    $seg = $Segundos
    if ($seg -eq 0) { $seg = [int](Get-WAProp $cfg 'intervalo_segundos' 10) }
    if ($seg -lt 5) { $seg = 5 }  # menos de 5 s castiga a Zernio sin mejorar la demo
    if ($Oculto) {
        if ($cfg.automatico_habilitado -ne $true) { return }
    } else {
        Clear-Host
        Write-Host '=== ASISTENTE WHATSAPP (HACKATHON) - BUCLE EN ESTA VENTANA ===' -ForegroundColor Cyan
        Write-Host "Revisa cada $seg segundos mientras esta ventana este abierta. Para la demo usa mejor -ActivarFondo."
        if (-not (Read-WAConfirmacion 'AUTOMATICO' 'Escribe AUTOMATICO para arrancarlo (cualquier otra cosa = no)')) { Write-Host 'Cancelado.'; return }
        $cfg.automatico_habilitado = $true
        Write-WAJson $cfgPath $cfg
    }
    # Un solo bucle a la vez (el oculto de la tarea o el de una ventana).
    $mBucle = New-Object System.Threading.Mutex($false, ($script:WAInstancia.mutex + '_Bucle'))
    if (-not $mBucle.WaitOne(0)) {
        $mBucle.Dispose()
        if (-not $Oculto) { Write-Host 'Ya hay un bucle en marcha (probablemente el de fondo). Usa -Monitor para verlo.' -ForegroundColor Yellow }
        return
    }
    $dirReg = Join-Path $raiz 'registro'
    if (-not (Test-Path $dirReg)) { New-Item -ItemType Directory -Path $dirReg -Force | Out-Null }
    $diaReg = $null
    try {
        Write-WALog '-' 'BUCLE_INICIADO' ("Cada $seg segundos" + $(if ($Oculto) { ' (oculto)' } else { ' (ventana)' }))
        $latido = (Get-Date).AddMinutes(-2)
        while ($true) {
            $hoy = (Get-Date).ToString('yyyy-MM-dd')
            if ($hoy -ne $diaReg) {
                if ($diaReg) { try { Stop-Transcript | Out-Null } catch { } }
                Start-Transcript -Path (Join-Path $dirReg ('bucle-' + $hoy + '.txt')) -Append | Out-Null
                $diaReg = $hoy
            }
            $cfgAhora = Read-WAJson $cfgPath
            if ($cfgAhora.automatico_habilitado -ne $true) { Write-Host ((Get-Date).ToString('HH:mm:ss') + ' Parado con -Parar.'); break }
            try {
                $resultados = @(Invoke-WACiclo $raiz $true $true)
                foreach ($r in $resultados) {
                    if ($r.accion -ne 'NINGUNA') { Write-Host ((Get-Date).ToString('HH:mm:ss') + ' [' + $r.accion + '] estado=' + $r.estado + ' :: ' + $r.detalle) }
                }
                if (((Get-Date) - $latido).TotalSeconds -ge 60) {
                    $latido = Get-Date
                    Write-Host ((Get-Date).ToString('HH:mm:ss') + " En marcha: $($resultados.Count) chat(s) revisados en la ultima vuelta.")
                }
            } catch {
                $msg = $_.Exception.Message
                if ($msg -ne 'YA_HAY_UN_CICLO_EN_EJECUCION') { Write-Host ((Get-Date).ToString('HH:mm:ss') + ' CICLO CON ERROR: ' + $msg + ' (se reintenta)') }
            }
            Start-Sleep -Seconds $seg
        }
    } finally {
        if ($diaReg) { try { Stop-Transcript | Out-Null } catch { } }
        $mBucle.ReleaseMutex(); $mBucle.Dispose()
    }
    return
}
if ($ActivarAutomatico) {
    $cfgPath = Join-Path $raiz 'config.json'
    $cfg = Read-WAJson $cfgPath
    if ($cfg.modo -ne 'produccion') { Write-Host 'Primero activa la produccion (-ActivarProduccion).' -ForegroundColor Red; return }
    if ($null -eq (Get-WAWebhook)) { Write-Host 'Primero configura y prueba el aviso de Teams (-ConfigurarAviso y -ProbarAviso).' -ForegroundColor Red; return }
    # Intervalo: el indicado con -Minutos, o el guardado en la configuracion, o 5 por defecto.
    $intervalo = $Minutos
    if ($intervalo -eq 0) { $intervalo = [int](Get-WAProp $cfg 'intervalo_minutos' 5) }
    if ($SinSesion) {
        Write-Host "El asistente respondera y creara oportunidades SOLO, cada $intervalo minuto(s), TAMBIEN sin sesion iniciada (por ejemplo tras un reinicio)."
        Write-Host 'Windows guardara tu contrasena en el Programador de tareas. Si cambias la contrasena, vuelve a ejecutar este comando.'
    } else {
        Write-Host "El asistente respondera y creara oportunidades SOLO, cada $intervalo minuto(s), mientras tu sesion de Windows este abierta."
    }
    Write-Host 'Para pararlo en cualquier momento: -Parar'
    if (-not (Read-WAConfirmacion 'AUTOMATICO' 'Escribe AUTOMATICO para activarlo (cualquier otra cosa = no)')) { Write-Host 'Cancelado.'; return }
    # Se lanza a traves de wscript.exe y un pequeno .vbs para que no aparezca ninguna ventana cada 5 minutos.
    $vbs = Join-Path $raiz 'HACK-Ciclo-Oculto.vbs'
    if (-not (Test-Path -LiteralPath $vbs)) { Write-Host 'Falta HACK-Ciclo-Oculto.vbs en la carpeta ciclo.' -ForegroundColor Red; return }
    $accion = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument ('//B //Nologo "' + $vbs + '"')
    # Dos disparadores: cada 5 minutos y, ademas, al iniciar sesion (tras reiniciar el equipo arranca solo).
    $quien = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    $disparo = @(
        (New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $intervalo)),
        (New-ScheduledTaskTrigger -AtLogOn -User $quien)
    )
    $ajustes = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 4) -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    if ($SinSesion) {
        # La tarea se ejecuta con tu usuario aunque nadie haya iniciado sesion: Windows guarda la contrasena
        # (el ciclo no la ve ni la guarda). Asi se pueden leer las claves cifradas y usar Hermes tras un reinicio.
        # Se pide en la propia consola (Get-Credential abre una ventana que puede quedar escondida detras).
        Write-Host "Usuario: $quien"
        $segura = Read-Host 'Escribe tu contrasena de Windows (no se mostrara) y pulsa Intro' -AsSecureString
        if ($null -eq $segura -or $segura.Length -eq 0) { Write-Host 'Cancelado: contrasena vacia.'; return }
        $cred = New-Object System.Management.Automation.PSCredential($quien, $segura)
        $disparo = @($disparo[0])
        try {
            Register-ScheduledTask -TaskName $tarea -Action $accion -Trigger $disparo -Settings $ajustes -User $quien `
                -Password $cred.GetNetworkCredential().Password -RunLevel Limited -Force -ErrorAction Stop | Out-Null
        } catch {
            Write-Host ('No se pudo registrar la tarea sin sesion: ' + $_.Exception.Message) -ForegroundColor Red
            Write-Host 'Puede que la contrasena no sea correcta o que una directiva de la empresa no lo permita. La tarea anterior sigue igual.'
            return
        } finally { $cred = $null }
    } else {
        $usuario = New-ScheduledTaskPrincipal -UserId $quien -LogonType Interactive -RunLevel Limited
        Register-ScheduledTask -TaskName $tarea -Action $accion -Trigger $disparo -Settings $ajustes -Principal $usuario -Force | Out-Null
    }
    $cfg.automatico_habilitado = $true
    Set-WAProp $cfg 'intervalo_minutos' $intervalo
    Write-WAJson $cfgPath $cfg
    Write-WALog '-' 'AUTOMATICO_ACTIVADO' ("Cada $intervalo minuto(s)" + $(if ($SinSesion) { ', sin necesidad de sesion' } else { '' }))
    Write-Host "Automatico ACTIVADO cada $intervalo minuto(s). Primera ejecucion en 1 minuto." -ForegroundColor Green
    return
}

if ($ActivarProduccion) {
    # Pasa a leer TODOS los chats nuevos de WhatsApp desde este momento. No activa envios automaticos:
    # sin -Ejecutar solo se revisa; con -Ejecutar se pide ENVIAR/CREAR en cada accion.
    $cfgPath = Join-Path $raiz 'config.json'
    $cfg = Read-WAJson $cfgPath
    if ($cfg.modo -eq 'produccion') { Write-Host ('Ya esta en produccion desde ' + $cfg.inicio_produccion_utc); return }
    Write-Host 'Desde ahora el ciclo leera los chats NUEVOS de WhatsApp (los anteriores se consideran existentes).'
    Write-Host 'No se envia nada sin -Ejecutar y sin escribir ENVIAR o CREAR.'
    if (-not (Read-WAConfirmacion 'PRODUCCION' 'Escribe PRODUCCION para activarlo (cualquier otra cosa = no)')) { Write-Host 'Cancelado.'; return }
    $cfg.modo = 'produccion'
    Set-WAProp $cfg 'inicio_produccion_utc' (Format-WAFecha (Get-WAAhora))
    Write-WAJson $cfgPath $cfg
    Write-WALog '-' 'PRODUCCION_ACTIVADA' $cfg.inicio_produccion_utc
    Write-Host ('Produccion activada. Inicio: ' + $cfg.inicio_produccion_utc) -ForegroundColor Green
    return
}

if ($Revisiones) {
    $lista = @(Get-WARevisiones | Sort-Object { $_.actualizado_utc })
    if ($lista.Count -eq 0) { Write-Host 'No hay conversaciones pendientes de revision.' -ForegroundColor Green; return }
    foreach ($e in $lista) {
        Write-Host ''
        Write-Host ('ID: ' + $e.conversation_id.Substring($e.conversation_id.Length - 6) + $(if ($e.prueba) { '  (' + $script:WAInstancia.prefijo_prueba + ')' } else { '' })) -ForegroundColor Cyan
        Write-Host ('  Desde:   ' + (ConvertTo-WAFecha $e.actualizado_utc).ToLocalTime().ToString('dd/MM/yyyy HH:mm'))
        Write-Host ('  Motivo:  ' + $e.motivo)
        if ($e.servicio) { Write-Host ('  Consulta: ' + $e.servicio) }
        if ($e.nombre) { Write-Host ('  Nombre:  ' + $e.nombre) }
    }
    Write-Host ''
    Write-Host 'Para cerrarla:  -Ignorar <ID>   |   Para devolverla al asistente:  -Retomar <ID>'
    return
}

if ($Ignorar -or $Retomar) {
    $script:WA.Config = Read-WAJson (Join-Path $raiz 'config.json')
    if ($Retomar) {
        Write-Host 'El asistente volvera a atender esta conversacion y respondera al proximo mensaje del contacto.'
        if (-not (Read-WAConfirmacion 'RETOMAR' 'Escribe RETOMAR para confirmarlo (cualquier otra cosa = no)')) { Write-Host 'Cancelado.'; return }
        $e = Resolve-WARevision $Retomar 'Retomar' $Nota
        Write-Host ('Devuelta al asistente: ' + $e.conversation_id) -ForegroundColor Green
    } else {
        $e = Resolve-WARevision $Ignorar 'Ignorar' $Nota
        Write-Host ('Revision cerrada: el asistente no volvera a intervenir en ' + $e.conversation_id) -ForegroundColor Green
    }
    return
}

if ($Reabrir) {
    # Devuelve a CAPTANDO las conversaciones de prueba que esten en REVISION (tras revisarlas una persona).
    $cfg = Read-WAJson (Join-Path $raiz 'config.json')
    foreach ($cid in @($cfg.conversaciones_prueba)) {
        $e = Read-WAJson (Get-WARutaConv $cid)
        if ($null -eq $e -or $e.estado -ne 'REVISION') { Write-Host 'La conversacion de prueba no esta en REVISION: nada que reabrir.'; continue }
        Write-Host ('Motivo de la revision: ' + $e.motivo)
        if (-not (Read-WAConfirmacion 'REABRIR' 'Escribe REABRIR para que el asistente retome esta conversacion (cualquier otra cosa = no)')) { Write-Host 'Cancelado.'; continue }
        Set-WAEstado $e 'CAPTANDO' 'Reabierta manualmente tras revision'
        Save-WAEstadoConv $e
        Write-Host 'Reabierta. Ejecuta de nuevo el ciclo con -Ejecutar.' -ForegroundColor Green
    }
    return
}

if ($Estado) {
    $dir = Join-Path $raiz 'estado\conversaciones'
    if (-not (Test-Path $dir)) { Write-Host 'Sin conversaciones registradas.'; return }
    Get-ChildItem $dir -Filter '*.json' | ForEach-Object {
        $e = Read-WAJson $_.FullName
        [pscustomobject]@{
            Conversacion = $e.conversation_id.Substring(0, 6) + '...'
            Prueba = $e.prueba; Estado = $e.estado; Respuestas = $e.respuestas_enviadas
            Nombre = $e.nombre; Email = $e.email; Oportunidad = $e.opportunity_id; Motivo = $e.motivo
        }
    } | Format-List
    return
}

if ($Automatico) {
    # Ejecucion programada: sin preguntas, con registro diario de lo mostrado.
    $dirReg = Join-Path $raiz 'registro'
    if (-not (Test-Path $dirReg)) { New-Item -ItemType Directory -Path $dirReg -Force | Out-Null }
    Start-Transcript -Path (Join-Path $dirReg ('ejecuciones-' + (Get-Date).ToString('yyyy-MM-dd') + '.txt')) -Append | Out-Null
    try { $resultados = Invoke-WACiclo $raiz $true $true }
    catch { Write-Host ('CICLO DETENIDO: ' + $_.Exception.Message); $resultados = @() }
    foreach ($r in $resultados) { if ($r.accion -ne 'NINGUNA') { Write-Host ('[' + $r.accion + '] estado=' + $r.estado + ' :: ' + $r.detalle) } }
    Stop-Transcript | Out-Null
    return
}

Clear-Host
Write-Host '=== ASISTENTE WHATSAPP (HACKATHON) - CICLO ===' -ForegroundColor Cyan
Write-Host ('Modo: ' + $(if ($Ejecutar) { 'EJECUTAR (pide confirmacion antes de enviar o crear)' } else { 'REVISAR (no envia ni crea nada)' }))
$resultados = Invoke-WACiclo $raiz $Ejecutar.IsPresent $Automatico.IsPresent
Write-Host ''
Write-Host '=== RESUMEN ===' -ForegroundColor Cyan
foreach ($r in $resultados) {
    Write-Host ('[' + $r.accion + '] estado=' + $r.estado + ' :: ' + $r.detalle)
}
$c = $script:WA.Contadores
Write-Host ("Llamadas -> Zernio GET: {0} | Zernio envios: {1} | ERP consultas: {2} | ERP altas: {3} | Hermes: {4} | Avisos Teams: {5}" -f $c.GET, $c.POST, $c.BALTER_LECTURAS, $c.BALTER_ALTAS, $c.HERMES, $c.AVISOS)

' Asistente WhatsApp (hackathon) - lanza el BUCLE oculto (revision cada pocos segundos) sin abrir ninguna ventana.
' Lo ejecuta la tarea programada; mientras el bucle vive, la tarea no lanza otro (IgnoreNew). Si cae, lo relanza.
Option Explicit
Dim sh, fso, carpeta, cmd
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
carpeta = fso.GetParentFolderName(WScript.ScriptFullName)
cmd = "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File " & Chr(34) & carpeta & "\HACK-Ciclo.ps1" & Chr(34) & " -Bucle -Oculto"
WScript.Quit sh.Run(cmd, 0, True)

' Asistente WhatsApp (hackathon) - lanza el ciclo automatico sin abrir ninguna ventana.
' La tarea programada ejecuta este archivo con wscript.exe; PowerShell se abre oculto (0) y se espera a que termine.
Option Explicit
Dim sh, fso, carpeta, cmd
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
carpeta = fso.GetParentFolderName(WScript.ScriptFullName)
cmd = "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -File " & Chr(34) & carpeta & "\HACK-Ciclo.ps1" & Chr(34) & " -Ejecutar -Automatico"
WScript.Quit sh.Run(cmd, 0, True)

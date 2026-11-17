' Study Desk launcher for Windows: starts the server if it is not already up and
' opens the app in its own window, with no console window. The desktop shortcut
' made by make_shortcut.ps1 points here.
'
'   wscript launch.vbs ["<study folder>" [<port>]]
'
' Every path is worked out from where this script sits.
Option Explicit
Dim fso, shell, here, serve, tail, i
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
here = fso.GetParentFolderName(WScript.ScriptFullName)
serve = fso.BuildPath(fso.GetParentFolderName(here), "serve.py")
tail = " """ & serve & """ --background --window app --dialog"
If WScript.Arguments.Count > 0 Then tail = tail & " --folder """ & WScript.Arguments(0) & """"
If WScript.Arguments.Count > 1 Then tail = tail & " --port " & CLng(WScript.Arguments(1))

' The Python launcher first (python.org installs it), then python on PATH.
On Error Resume Next
shell.Run "pyw -3" & tail, 0, False
If Err.Number <> 0 Then
  Err.Clear
  shell.Run "pythonw" & tail, 0, False
End If
If Err.Number <> 0 Then
  MsgBox "Study Desk needs Python 3.10 or later (python.org). It was not found.", 16, "Study Desk"
End If

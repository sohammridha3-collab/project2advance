Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get project folder directory
strScriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Check if port 8000 is already in use
Set objExec = objShell.Exec("netstat -ano")
strNetstat = objExec.StdOut.ReadAll()

If InStr(strNetstat, ":8000 ") = 0 Then
    ' Port 8000 is free, launch uvicorn completely silently (window style 0, no wait)
    objShell.CurrentDirectory = strScriptDir
    strCmd = "powershell -WindowStyle Hidden -NoProfile -Command ""python -m uvicorn main:app --host 127.0.0.1 --port 8000"""
    objShell.Run strCmd, 0, False
End If

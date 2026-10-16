Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strScriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
objShell.CurrentDirectory = strScriptDir

' Run start_service.bat completely hidden (0 = SW_HIDE, False = don't wait)
objShell.Run "cmd.exe /c start_service.bat", 0, False

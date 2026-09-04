Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
currDir = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currDir

pywPath = currDir & "\python\pythonw.exe"
If Not FSO.FileExists(pywPath) Then
    pywPath = "pythonw.exe"
End If

scriptPath = currDir & "\main.py"
WshShell.Run Chr(34) & pywPath & Chr(34) & " " & Chr(34) & scriptPath & Chr(34), 0, False

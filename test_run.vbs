Set WshShell = CreateObject("WScript.Shell")
dir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = dir
WScript.Echo "CurrentDir: " & WshShell.CurrentDirectory
On Error Resume Next
res = WshShell.Run("python\pythonw.exe app.py", 0, True)
If Err.Number <> 0 Then
    WScript.Echo "Error: " & Err.Description & " (" & Err.Number & ")"
Else
    WScript.Echo "Run returned: " & res
End If

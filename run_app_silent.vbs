Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = ScriptDir
WshShell.Environment("PROCESS")("HG_LICENSE_DISABLED") = "1"
WshShell.Environment("PROCESS")("PYTHONUTF8") = "1"
WshShell.Environment("PROCESS")("PYTHONIOENCODING") = "utf-8"
WshShell.Run """" & ScriptDir & "\python\pythonw.exe"" """ & ScriptDir & "\app.py""", 0, False

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\terada\Desktop\apps\体組成管理app"
WshShell.Run "python health_data_server.py", 0, False
# Spool-Maker
A PyQt5 UI for reading/writing custom Ultimaker NFC Material Spools

This GUI/set of scripts is based on some classes written by @gandy92 here: https://gist.github.com/gandy92/a7eef12009045f7b3fc01d778c3b79a7

I have added to his work but designing a small GUI, adding some more functions for reading existing/editing spools, and for automatically looking up materials from the Ultimaker Cura slicer.

Please also see: https://community.ultimaker.com/topic/19648-readwrite-nfc-tags/ for its purpose.

Note: If using Linux, you will need to provide the system materials directly in the CuraMaterial.py file before these materials will appear in the list.
I don't have a linux machine to determine where the Cura directory is at this time.

Install Instructions (Running from script):
-------------------------------------------------------
1. Extract the python scripts to a folder of your choice, and open a terminal/powershell/cmd window in this folder.

2. Install dependencies with the following command:
	Windows: 'pip3 install PyQt5 numpy pyscard crc8 ndef nfcpy'
	MacOS/Linux: 'sudo pip3 install PyQt5 numpy pyscard crc8 ndef nfcpy'

3. Run the following command to launch: 'python3 SpoolMaker.py'



To compile an exe version with pyinstaller (Windows):
-------------------------------------------------------
1. Extract the python scripts to a folder of your choice, and open a terminal/powershell/cmd window in this folder.

2. Run the following command: 'pyinstaller.exe --onefile --windowed --icon=.\icon.ico --add-data="gui.ui;." .\SpoolMaker.py'

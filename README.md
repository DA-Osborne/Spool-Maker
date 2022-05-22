# Spool-Maker
A PyQt5 UI for reading/writing custom Ultimaker NFC Material Spools

This GUI/set of scripts is based on some classes written by @gandy92 here: https://gist.github.com/gandy92/a7eef12009045f7b3fc01d778c3b79a7

I have added to his work by designing a small GUI, adding some more functions for reading/editing spools, and for automatically looking up materials from the Ultimaker Cura slicer.

Tested with the ACR122U SmartCard reader. (Usually available on Amazon and eBay)
To use, place an NTAG216 compatible tag (sometimes referred to as a MIFARE Ultralight tag) on the reader.

Use the 'Read Tag' button to read the material on a tag, and the 'Write Tag' button to write the selected material to a tag.
You can also overwrite used UM spools. The ACR122U will beep once complete.

Please also see: https://community.ultimaker.com/topic/19648-readwrite-nfc-tags/ for its purpose.

Install Instructions (Running from script):
-------------------------------------------------------
1. Extract the python scripts to a folder of your choice and open a Terminal/PowerShell/CMD window in this folder.

2. Install dependencies with the following command:
    - 'pip3 install PyQt5 numpy pyscard crc8 ndef nfcpy'

3. Plug in your smartcard reader (if you do not do this first, you can sometimes get an exception)

4. Run the following command to launch: 'python3 SpoolMaker.py'


To compile an exe version with pyinstaller (Windows):
-------------------------------------------------------
1. Extract the python scripts to a folder of your choice, and open a terminal/powershell/cmd window in this folder.

2. Install pyinstaller

3. Run the following command: 'pyinstaller.exe --onefile --windowed --icon=.\icon.ico --add-data="icon.ico;." --add-data="gui.ui;." .\SpoolMaker.py'

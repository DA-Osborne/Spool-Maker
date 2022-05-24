# Spool-Maker
## *A PyQt5 UI for reading/writing custom Ultimaker NFC Material Spools*
 
This GUI/set of scripts is based on some classes written by @gandy92 here: https://gist.github.com/gandy92/a7eef12009045f7b3fc01d778c3b79a7
 
I have added to his work by designing a small GUI, adding some more functions for reading/editing spools, and for automatically looking up materials from the Ultimaker Cura slicer.

### Hardware
A computer running Windows, Mac or Linux based machine (including Raspberry Pi)
ACR122U SmartCard reader. (Usually available on Amazon and eBay. Other readers may work, but we not tested)

### Use
1. Place a NTAG216 compatible tag (also referred to as a MIFARE Ultralight tag) on the reader.
 
2. Use the 'Read Tag' button to read the material on a tag, and the 'Write Tag' button to write the selected material to a tag.

*Note: You can also overwrite used UM spools. The ACR122U will beep once complete.*
 
*See: https://community.ultimaker.com/topic/19648-readwrite-nfc-tags/ for more information/its purpose.*

## Install Instructions 
### Running from script

1. Extract the python scripts to a folder of your choice and open a **Terminal/PowerShell/CMD** window in this folder.

2. Install dependencies with the following command:
<code> pip3 install PyQt5 numpy pyscard crc8 ndef nfcpy </code>

3. Plug in your smartcard reader (if you do not do this first, you may get an error)

4. Run the following command to launch: 
<code> 'python3 SpoolMaker.py' </code>

### To compile an exe version with pyinstaller (Windows):

- *From the same folder...*

1. Install pyinstaller

2. Run the following command:
<code> pyinstaller.exe --onefile --windowed --icon=.\icon.ico --add-data="icon.ico;." --add-data="gui.ui;." .\SpoolMaker.py </code>

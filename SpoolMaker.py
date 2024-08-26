#!/usr/bin/env python3
''' Spool Maker - A package for reading/writing Ultimaker compatible NFC filament tags.
Requires a smartcard reader/writer. Tested with the ACR122U-A9 on Windows 10, 21H1.
Compatible with NTAG216 MIFARE Ultralight.

Uses PyQt5 for GUI, or can be run from a terminal using the customisable variables at the end.
Note: Connect the reader before loading the application!

Thanks to:
Thanks to Maeven-Black (GitHub) for supplying fix for high DPI screens.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

# /---------------------------------\
#|          Import Modules           |
# \---------------------------------/
import sys
import os
import time

from PyQt5 import QtWidgets, QtGui, uic, QtCore

import CuraMaterial as c
import NFCSpool as s

__author__ = 'Dale A. Osborne'
__copyright__ = 'Copyright 2021, Dale Osborne'
__license__ = 'GPL'
__version__ = '1.1.5'



# /---------------------------------\
#|       Functions & Variables       |
# \---------------------------------/

# Enable high DPI Scaling for the GUI
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

# Resource loader for loading UI file with PyInstaller dist
def resource_path(relPath):
    try:
        basePath = sys._MEIPASS
    except Exception:
        basePath = os.path.abspath('.')
    return os.path.join(basePath, relPath)



# /---------------------------------\
#|          GUI Class (PyQt)         |
# \---------------------------------/
class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(resource_path('gui.ui'), self)
        self.setWindowIcon(QtGui.QIcon(resource_path('icon.ico')))

        # Load installed materials
        self.curaMaterials, self.mList, self.mDia = c.get_all_materials()
        self.curaAllMaterials, self.mList, self.mDia = c.get_all_materials()

        # Material Selector
        self.materialSelect = self.findChild(QtWidgets.QComboBox, 'combo_matSelector')
        self.matFilt = self.findChild(QtWidgets.QLineEdit, 'material_filter')
        self.matFilt.textChanged.connect(self.filterChanged)
        self.matDia = self.findChild(QtWidgets.QComboBox, 'material_diameter')
        self.matDia.currentIndexChanged.connect(self.filterChanged)

        if self.mDia is not None:
            self.mDiaKeys = list(self.mDia);
            self.mDiaKeys.sort()
            self.matDia.addItems(self.mDiaKeys)
            self.matDia.setCurrentIndex(self.mDiaKeys.index("2.85"))

        if self.mList is not None:
            self.materialSelect.addItems(self.mList)
        self.materialSelect.currentIndexChanged.connect(self.materialSelectionChange)
        
        # Material Information
        self.infoBrand = self.findChild(QtWidgets.QLineEdit, 'line_brand')
        self.infoBrand.setText(self.curaMaterials[0].brand)
        self.infoMaterial = self.findChild(QtWidgets.QLineEdit, 'line_material')
        self.infoMaterial.setText(self.curaMaterials[0].material)
        self.infoColor = self.findChild(QtWidgets.QLineEdit, 'line_color')
        self.infoColor.setText(self.curaMaterials[0].color)
        self.infoGUID = self.findChild(QtWidgets.QLineEdit, 'line_guid')
        self.infoGUID.setText(self.curaMaterials[0].guid)

        # NFC Tag Information
        self.tagStatus = self.findChild(QtWidgets.QLineEdit, 'line_nfcStatus')
        self.tagSerial = self.findChild(QtWidgets.QLineEdit, 'line_serial')
        self.tagBrand = self.findChild(QtWidgets.QLineEdit, 'line_cbrand')
        self.tagMaterial = self.findChild(QtWidgets.QLineEdit, 'line_cmaterial')
        self.tagColor = self.findChild(QtWidgets.QLineEdit, 'line_ccolor')
        self.tagGUID = self.findChild(QtWidgets.QLineEdit, 'line_cguid')
        self.tagTWeight = self.findChild(QtWidgets.QLineEdit, 'line_totalweight')
        self.tagRWeight = self.findChild(QtWidgets.QLineEdit, 'line_remainweight')
        self.tagTime = self.findChild(QtWidgets.QLineEdit, 'line_printtime')

        self.newWeight = self.findChild(QtWidgets.QLineEdit, 'line_nweight')


        self.status = self.findChild(QtWidgets.QLineEdit, 'line_status')
        self.statusColor = self.findChild(QtWidgets.QProgressBar, 'progressBar')
        
        # Buttons
        self.btnRead = self.findChild(QtWidgets.QPushButton, 'btn_read')
        self.btnRead.clicked.connect(self.readTag)
        self.btnWrite = self.findChild(QtWidgets.QPushButton, 'btn_write')
        self.btnWrite.clicked.connect(self.writeTag)

        # Menu Actions
        self.actionExit = self.findChild(QtWidgets.QAction, 'actionExit')
        self.actionExit.triggered.connect(self.exit)
        self.actionRescan = self.findChild(QtWidgets.QAction, 'actionRescan_Materials')
        self.actionRescan.triggered.connect(self.rescan)
        self.actionRead = self.findChild(QtWidgets.QAction, 'actionRead_Tag')
        self.actionRead.triggered.connect(self.readTag)
        self.actionWrite = self.findChild(QtWidgets.QAction, 'actionWrite_Tag')
        self.actionWrite.triggered.connect(self.writeTag)

        # Show UI
        self.show()
        self.setStatus('Ready', True)

    def exit(self):
        print('Exiting')
        self.close()

    def rescan(self):
        # Load installed materials
        print('Reloading Cura materials...', end = '')
        self.curaMaterials, self.mList, self.mDia = c.get_all_materials(self.matFilt.text(), self.mDiaKeys[self.matDia.currentIndex()])
        self.materialSelect.clear()
        if self.mList is not None:
            self.materialSelect.addItems(self.mList)
        print('Done!')

    def filterChanged(self):
        self.rescan()

    def materialSelectionChange(self, i):
        print(i)
        if i < 0:
            self.infoBrand.setText("")
            self.infoMaterial.setText("")
            self.infoColor.setText("")
            self.infoGUID.setText("")
        else:
            self.infoBrand.setText(self.curaMaterials[i].brand)
            self.infoMaterial.setText(self.curaMaterials[i].material)
            self.infoColor.setText(self.curaMaterials[i].color)
            self.infoGUID.setText(self.curaMaterials[i].guid)
    
    def readTag(self, post_write=False):
        print('Reading Tag...')
        if not post_write:
            self.setStatus('Waiting for tag...', False)
        cardStatus, uid, guid, total, remain, time = s.readSpool(ui=True)
        if uid is not None:
            self.tagSerial.setText(':'.join([uid[i:i+2] for i,j in enumerate(uid) if not (i%2)]))
            if cardStatus == 0:
                self.tagStatus.setText('Valid Spool Tag')
                self.tagGUID.setText(guid)
                self.tagTWeight.setText(str(total))
                self.tagRWeight.setText(str(remain))
                self.tagTime.setText(str(time))
                
                # Lookup material based on the GUID read from the tag
                materialData = self.lookupMaterial(guid)
                self.tagBrand.setText(materialData[0])
                self.tagMaterial.setText(materialData[1])
                self.tagColor.setText(materialData[2])
                if not post_write:
                    self.setStatus('Tag Read Successful', True)

            elif cardStatus == 1:
                self.tagStatus.setText('Blank Tag/Unknown Data')
                if not post_write:
                    self.setStatus('Tag Read Successful', True)

            elif cardStatus == 2:
                print('Tag was removed early')
                self.setStatus('Tag Removed!', False)
        else:
            print('Read timed out')
            self.setStatus('Tag Read Timed Out', False)

    def writeTag(self):
        print('Writing Tag...')
        self.setStatus('Writing New Tag...', False)
        guid = self.curaMaterials[self.materialSelect.currentIndex()].guid
        unit = 2#mg
        weight = int(self.newWeight.text())
        s.writeSpool(guid, unit, weight)
        time.sleep(1) # Wait 1 second
        self.setStatus('Tag Write Successful', True)
        self.readTag(True) # Read tag which should now contain the new data
        
    def setStatus(self, text:str, colorOn:bool):
        self.status.setText(text)
        if colorOn:
            self.statusColor.setValue(100)
        else:
            self.statusColor.setValue(0)
    
    def lookupMaterial(self, guid:str):
        print('Finding: {}'.format(guid))
        for material in self.curaAllMaterials:
            if material.guid == guid:
                print('Found: {} {} {} {}'.format(material.brand,material.material,material.color,material.guid))
                return [material.brand, material.material, material.color]
        return ['!!', 'Material not in database', '!!']

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()

if __name__ == '__main__':
    main()

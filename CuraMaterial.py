#!/usr/bin/env python3
''' CuraMaterial - A package for reading installed Cura Materials.
A part of the Spool Maker package.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Thanks to:
Thanks to Maeven-Black (GitHub) for supplying fix for newer versions of Ultimaker Cura.

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
import os
from sys import exit

import re
import platform
from pathlib import Path

__author__ = 'Dale A. Osborne'
__copyright__ = 'Copyright 2021, Dale Osborne'
__license__ = 'GPL'
__version__ = '1.1.5'



# /---------------------------------\
#|          Get Cura Config          |
# \---------------------------------/
# Windows
if platform.system() == 'Windows':
    from winreg import HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE, KEY_READ, OpenKey, QueryValueEx, EnumKey, QueryInfoKey
    
    def getLatestKey(hKey):
        curaList = []
        for i in range(0, QueryInfoKey(hKey)[0]):
            curaList.append(EnumKey(hKey, i))
        
        fList = [k for k in curaList if 'Ultimaker Cura' in k]
        fList.sort()
        return fList[-1]
    
    # Get Cura User Directory
    CURA_USER_DIR = os.path.join(os.getenv('APPDATA'), 'cura')
    CURA_CONFIGS = [f.name for f in os.scandir(CURA_USER_DIR) if f.is_dir()]
    CURA_CONFIGS.sort(key=lambda x:int(x.replace(".","" if len(x)>3 else "0")))
    CURA_USER_MAT_DIR = os.path.join(CURA_USER_DIR, CURA_CONFIGS[-1], 'materials')

    # Get Cura Install Directory
    latestInstalled = None
    curaSysDir = None
    
    try:
        # Search for Cura >= v5.3 version
        access_key = OpenKey(HKEY_LOCAL_MACHINE, 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths', 0, KEY_READ)
        curaList = []
        for i in range(0, QueryInfoKey(access_key)[0]):
            curaList.append(EnumKey(access_key, i))
            fList = [k for k in curaList if 'UltiMaker Cura' in k]
            fList.sort()
        curaSysDirKey = OpenKey(HKEY_LOCAL_MACHINE,"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\" + fList[-1], 0, KEY_READ)
        curaSysDir = os.path.dirname(QueryValueEx(curaSysDirKey, '')[0])
        latestInstalled = 5
    except:
        try:
            # Search for Cura >= v5.0 <= 5.2.1 version
            curaSysDirKey = OpenKey(HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\Ultimaker-Cura.exe\\', 0, KEY_READ)
            curaSysDir = os.path.dirname(QueryValueEx(curaSysDirKey, '')[0])
            latestInstalled = 5
        except:
            try:
                # Search for Cura <= v4.13.1
                latestVersion = getLatestKey(OpenKey(HKEY_LOCAL_MACHINE, 'SOFTWARE\\WOW6432Node\\Ultimaker B.V.', 0, KEY_READ))
                curaSysDirKey = OpenKey(HKEY_LOCAL_MACHINE, 'SOFTWARE\\WOW6432Node\\Ultimaker B.V.\\' + latestVersion, 0, KEY_READ)
                curaSysDir = QueryValueEx(curaSysDirKey, '')[0]
            except:
                print('Failed to determine Ultimaker Cura install location')
                exit(1)
    
    CURA_INSTALL_DIR = curaSysDir
    if latestInstalled == 5:
        CURA_MAT_DIR = os.path.join(CURA_INSTALL_DIR, 'share', 'cura', 'resources', 'materials')
    else:
        CURA_MAT_DIR = os.path.join(CURA_INSTALL_DIR, 'resources', 'materials')

elif platform.system() == 'Darwin': # OS X
    # Get Cura User Directory
    CURA_USER_DIR = str(Path.home()) + '/Library/Application Support/cura/'
    CURA_CONFIGS = [f.name for f in os.scandir(CURA_USER_DIR) if f.is_dir()]
    CURA_CONFIGS.sort(key=lambda x:int(x.replace(".","" if len(x)>3 else "0")))
    CURA_USER_MAT_DIR = os.path.join(CURA_USER_DIR, CURA_CONFIGS[-1], 'materials')
    
    # Set Cura Install Directory
    CURA_MAT_DIR = '/Applications/Ultimaker Cura.app/Contents/Resources/resources/materials'

elif platform.system() == 'Linux':
    # Get Cura User Directory
    CURA_USER_DIR = str(Path.home()) + '/.local/share/cura/'
    CURA_CONFIGS = [f.name for f in os.scandir(CURA_USER_DIR) if f.is_dir()]
    CURA_CONFIGS.sort(key=lambda x:int(x.replace(".","" if len(x)>3 else "0")))
    CURA_USER_MAT_DIR = os.path.join(CURA_USER_DIR, CURA_CONFIGS[-1], 'materials')
    
    # Set Cura Install Directory
    CURA_MAT_DIR = str(Path.home()) + '/opt/UM/materials' # set a sensible default where AppInfo set can be placed

else:
    print('Unknown operating system. To override, remove the exit(1) command from the CuraMaterial script.')
    exit(1)

print('User Material Directory: ', CURA_USER_MAT_DIR)
print('System Material Directory: ', CURA_MAT_DIR)



# /---------------------------------\
#|              Classes              |
# \---------------------------------/
class curaMaterial():
    def __init__(self, brand:str, material:str, color:str, label:str, guid:str):
        self.brand = brand
        self.material = material
        self.color = color
        self.label = label #Label is used for custom materials. Without they are indistinguishable
        self.guid = guid 
        #Might as well process this once if we want to sort on it.
        self.allInfo = brand + ':' + material + ' ' + label + ' (' + color + ')' 



# /---------------------------------\
#|          Main Functions           |
# \---------------------------------/
def read_material(cm):
    '''Reads a cura material profile (.xml.fdm_material) and returns a curaMaterial object'''
    brand = material = color = label = guid = ''
    found = [False]*5 # Corresponds with above values. True once that value is found.
    with open(cm, 'r') as f:
        for line in f:
            if all(found):
                break
            if '<brand>' in line and not found[0]:
                data = re.split('<|>| ', line.strip())
                for b in data[2:]:
                    if b != '/brand':
                        brand += b
                    else:
                        break
                found[0] = True
                continue
            if '<material>' in line and not found[1]:
                data = re.split('<|>| ', line.strip())
                for m in data[2:]:
                    if m != '/material':
                        material += m
                    else:
                        break
                found[1] = True
                continue
            if '<color>' in line and not found[2]:
                data = re.split('<|>| ', line.strip())
                for c in data[2:]:
                    if c != '/color':
                        color += c
                    else:
                        break
                found[2] = True
                continue
            if '<label>' in line and not found[3]:
                data = re.split('<|>| ', line.strip())
                for l in data[2:]:
                    if l != '/label':
                        label += l
                    else:
                        break
                found[3] = True
                continue
            if '<GUID>' in line and not found[4]:
                guid = re.split('<|>| ', line.strip())[2]
                found[4] = True
                continue
    return curaMaterial(brand, material, color, label, guid)

def sortKey(e):
    return e.allInfo

def add_if_match(mList, root, file, filtStr):
    if file.endswith('.xml.fdm_material'):
        mat = read_material(os.path.join(root, file))
        if not any(ele.isupper() for ele in filtStr):
            matToSearch=mat.allInfo.lower()
        else:
            matToSearch=mat.allInfo
        if filtStr in matToSearch:
            mList.append(mat)

def get_all_materials(filtStr = ""):
    '''Reads all system and user cura materials, and returns a list of curaMaterial objects'''
    mList = [] # List of materials
    sList = [] # List of material names for QT combobox

    for root, _, files in os.walk(CURA_USER_MAT_DIR):
        for file in files:
            add_if_match(mList, root, file, filtStr)

    for root, _, files in os.walk(CURA_MAT_DIR):
        for file in files:
            add_if_match(mList, root, file, filtStr)
    mList.sort(key=sortKey)

    for mat in mList:
        sList.append(mat.allInfo)

    return mList, sList

if __name__ == '__main__':
    # If run directly, list installed materials
    materials, _ = get_all_materials()
    for material in materials:
        print('Material: ', material.brand, '/', material.material, '\t', material.color)
        print('\t', material.guid)

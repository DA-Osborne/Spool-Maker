#!/usr/bin/env python3
""" CuraMaterial - A package for reading installed Cura Materials.
A part of the Spool Maker package.

Dale A. Osborne, 2020

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
"""
# To-Do:
# - Auto detect OS X and Linux Cura directories. (I don't have acess to these OS' at the moment)



# /---------------------------------\
#|          Import Modules           |
# \---------------------------------/
import sys
import os
import re
import platform

from winreg import OpenKey, HKEY_LOCAL_MACHINE, QueryValueEx



# /---------------------------------\
#|          Get Cura Config          |
# \---------------------------------/
# Windows
if platform.system() == 'Windows':
    # Get Cura User Directory
    CURA_USER_DIR = os.path.join(os.getenv('APPDATA'), 'cura')
    CURA_CONFIGS = [f.name for f in os.scandir(CURA_USER_DIR) if f.is_dir()]
    CURA_CONFIGS.sort()
    CURA_USER_MAT_DIR = os.path.join(CURA_USER_DIR, CURA_CONFIGS[-1], 'materials')

    # Set Cura Install Directory
    curaSysDir = OpenKey(HKEY_LOCAL_MACHINE, 'SOFTWARE\\WOW6432Node\\Ultimaker B.V.\\Ultimaker Cura 4.7')
    CURA_INSTALL_DIR = QueryValueEx(curaSysDir, '')[0]
    CURA_MAT_DIR = os.path.join(CURA_INSTALL_DIR, 'resources', 'materials')

elif platform.system() == 'Darwin': # OS X
    # Replace with your user and system materials folders
    CURA_USER_MAT_DIR = '/Users/user/Library/Application\\ Support/Cura/4.7/'
    CURA_MAT_DIR = ''

elif platform.system() == 'Linux':
    # Replace with your user and system materials folders
    CURA_USER_MAT_DIR = '/home/user/.local/share/cura/4.7/materials'
    CURA_MAT_DIR = ''
else:
    print('Unknown operating system')
    exit(1)

print('User Material Directory: ', CURA_USER_MAT_DIR)
print('System Material Directory: ', CURA_MAT_DIR)



# /---------------------------------\
#|              Classes              |
# \---------------------------------/
class curaMaterial():
    def __init__(self, brand:str, material:str, color:str, guid:str):
        self.brand = brand
        self.material = material
        self.color = color
        self.guid = guid



# /---------------------------------\
#|          Main Functions           |
# \---------------------------------/
def read_material(cm):
    '''Reads a cura material profile (.xml.fdm_material) and returns a curaMaterial object'''
    brand = material = color = guid = ''
    found = [False]*4 # Corresponds with above values. True once that value is found.
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
            if '<GUID>' in line and not found[3]:
                guid = re.split('<|>| ', line.strip())[2]
                found[3] = True
                continue
    return curaMaterial(brand, material, color, guid)

def get_all_materials():
    '''Reads all system and user cura materials, and returns a list of curaMaterial objects'''
    mList = [] # List of materials
    sList = [] # List of material names for QT combobox

    for root, _, files in os.walk(CURA_USER_MAT_DIR):
        for file in files:
            if file.endswith('.xml.fdm_material'):
                mList.append(read_material(os.path.join(root, file)))
    for root, _, files in os.walk(CURA_MAT_DIR):
        for file in files:
            if file.endswith('.xml.fdm_material'):
                mList.append(read_material(os.path.join(root, file)))
    
    for mat in mList:
        sList.append(mat.brand + ':' + mat.material + ' (' + mat.color + ')')

    return mList, sList

if __name__ == '__main__':
    # If run directly, list installed materials
    materials, _ = get_all_materials()
    for material in materials:
        print('Material: ', material.brand, '/', material.material, '\t', material.color)
        print('\t', material.guid)

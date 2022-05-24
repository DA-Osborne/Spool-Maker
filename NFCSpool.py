#!/usr/bin/env python3
'''NFCSpool - A set of python classes and methods for writing custom ultimaker filament spools.

To use, place an NTAG216 compatible tag on the reader, edit the values in the 'custom spool maker' at
the end of this script, and run the script. The ACR122U will beep once complete. Imported by SpoolMaker
for use by the Spool Maker GUI.

Thanks to:
Developed from scripts by: @gandy, Ultimaker Public Forum, 2020
Thanks to Maker2 (Ultimaker Public Forum) for supplying a fix for running on MacOS

Useful Links used to construct this as a GUI:
https://community.ultimaker.com/topic/19648-readwrite-nfc-tags/
https://forum.dangerousthings.com/t/introduction-to-smart-card-development-on-the-desktop-guide/2744
http://www.unsads.com/specs/ISO/7816/ISO7816-4.pdf (The ISO standard)
https://pyscard.sourceforge.io/user-guide.html

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
import numpy as np

from smartcard.CardRequest import CardRequest
from smartcard.Exceptions import NoCardException, CardRequestTimeoutException
from smartcard.CardType import AnyCardType
from smartcard.System import readers
from smartcard import util

import uuid
from binascii import hexlify
from crc8 import crc8

from ndef import message
from ndef.record import GlobalRecord, Record

__author__ = 'Dale A. Osborne'
__copyright__ = 'Copyright 2021, Dale Osborne'
__license__ = 'GPL'
__version__ = '1.1.3'



# /---------------------------------\
#|             Variables             |
# \---------------------------------/
'''APDU Commands'''
get_uid = util.toBytes('FF CA 00 00 00')
beep = util.toBytes('FF 00 40 00 04 01 00 03 03')

'''APDU Responses'''
sucess = util.toBytes('90 00')
fail = util.toBytes('63 00')
notSupported = util.toBytes('6A 81')

TIMEOUT = 30 # How long to wait for a card in seconds
DEFAULT_SERIAL = '00:00:00:00:00:00:00'


# /---------------------------------\
#|              Classes              |
# \---------------------------------/
class MustBeEvenException(Exception):
    pass

class UltimakerMaterialRecord(GlobalRecord):
    _type = 'urn:nfc:ext:ultimaker.nl:material'
    _name = '1'

    NO_MATERIAL = uuid.UUID('00000000-0000-0000-0000-000000000000')

    def __init__(self, material_id=None, serial='', version=0, compat_version=0,
                 manufacturing_ts=0, station_id=0, batch_code=''):
        self._version = version
        self._compatibility_version = compat_version
        self._serial_number = serial
        self._manufacturing_timestamp = manufacturing_ts
        self._material_id = material_id if material_id is not None else self.NO_MATERIAL
        self._programming_station_id = station_id
        self._batch_code = batch_code

    def _encode_payload(self):
        data = self._encode_struct('>BB', self._version, self._compatibility_version)
        serial = self._serial_number.encode('utf-8') + b'\x00'*14
        data += serial[:14]
        data += self._encode_struct('>Q', self._manufacturing_timestamp)
        data += self._material_id.bytes
        data += self._encode_struct('>H', self._programming_station_id)
        data += self._batch_code.encode('utf-8')
        data += b'\x00' * 108

        return data[0:108]

    @classmethod
    def _decode_payload(cls, octets, errors):

        version, compat_version = cls._decode_struct('>BB', octets[0:2])
        serial_number = octets[2:16].decode('utf-8').split('\x00')[0]
        manufacturing_timestamp = cls._decode_struct('>Q', octets[16:24])
        material_id = uuid.UUID(bytes=octets[24:40])
        programming_station_id = cls._decode_struct('>H', octets[40:42])
        batch_code = octets[42:106].decode('utf-8').split('\x00')[0]

        return cls(material_id, serial_number, version, compat_version,
                   manufacturing_ts=manufacturing_timestamp, station_id=programming_station_id, batch_code=batch_code)

class UltimakerStatRecord(GlobalRecord):
    _type = 'urn:nfc:ext:ultimaker.nl:stat'
    _name = '2'

    MATERIAL_UNIT_UNUSED = 0
    MATERIAL_QUANTITY_LENGTH_MM = 1
    MATERIAL_QUANTITY_MASS_GR = 2
    MATERIAL_QUANTITY_VOLUME_CM3 = 3

    def __init__(self, material_total=0, material_unit=None, material_remaining=None, total_usage_duration=0,
                 version=0, compat_version=0):
        self._version = version
        self._compatibility_version = compat_version
        self._material_unit = material_unit if material_unit is not None else self.MATERIAL_UNIT_UNUSED
        self._material_total = material_total
        self._material_remaining = material_remaining if material_remaining is not None else material_total
        self._total_usage_duration = total_usage_duration
        self._unit = ['N/A', 'mm', 'mg', 'cm³'][self._material_unit]

    def _encode_payload(self):
        data = self._encode_struct('>BBBLLQ', self._version, self._compatibility_version, int(self._material_unit),
                                   self._material_total, self._material_remaining, self._total_usage_duration)
        data = data[:19] + crc8(data[:19]).digest()

        return data[0:20]

    @classmethod
    def _decode_payload(cls, octets, errors):

        version, compat_version, material_unit, material_total, material_remaining, total_usage_duration = \
            cls._decode_struct('>BBBLLQ', octets)

        crc = crc8(octets[:19]).digest()[0]
        if octets[19] != crc:
            print('  **** crc mismatch: tag={} self={}'.format(octets[19], crc))

        return cls(material_total=material_total, material_unit=material_unit, material_remaining=material_remaining,
                   total_usage_duration=total_usage_duration, version=version, compat_version=compat_version)

class SigRecord(GlobalRecord):
    _type = 'urn:nfc:wkt:Sig'

    _decode_min_payload_length = 2

    def __init__(self, sig):
        self._sig = sig

    def _encode_payload(self):
        return self._encode_struct('>H', self._sig)

    @classmethod
    def _decode_payload(cls, octets, errors):
        sig = cls._decode_struct('>H', octets)
        return cls(sig)

class MyFilamentSpool:
    def __init__(self, guid, serial, unit=2, weight=750000):
        self.material = UltimakerMaterialRecord(material_id=guid,
                                                serial=serial,
                                                batch_code='123456789AB',
                                                station_id=0xaffe)
        self.status = UltimakerStatRecord(material_unit=unit, material_total=weight)

    def data(self) -> bytes:
        encoder = message.message_encoder()
        results = list()
        encoder.send(None)
        encoder.send(self.material)
        results.append(encoder.send(SigRecord(0x2000)))
        results.append(encoder.send(self.status))
        results.append(encoder.send(self.status))
        results.append(encoder.send(None))

        result = b''.join(results)
        if len(result) % 4 != 0:
            print('Padding data with {} bytes to full page size.'.format(len(result) % 4))
            result += b'\x00' * (4-len(result) % 4)
        print('   Size is now {} bytes, that is {} pages with {} excess.'.format(len(result), len(result)//4, len(result) % 4))

        return result



# /---------------------------------\
#|         Register Classes          |
# \---------------------------------/
Record.register_type(UltimakerMaterialRecord)
Record.register_type(UltimakerStatRecord)
Record.register_type(SigRecord)



# /---------------------------------\
#|          Main Functions           |
# \---------------------------------/
def decode(octets, ui=False):
    '''Decodes UM spool binary to records'''
    records = message.message_decoder(octets, errors='relax')

    if ui:
        r_guid = ''
        r_total = 0
        r_remain = 0
        r_time = 0
        try:
            for record in records:
                if type(record) is UltimakerMaterialRecord:
                    r_guid = str(record._material_id)
                if type(record) is UltimakerStatRecord:
                    r_total = record._material_total
                    r_remain = record._material_remaining
                    r_time = record._total_usage_duration/3600
                    break
        except:
            return 1, r_guid, r_total, r_remain, r_time
        
        return 0, r_guid, r_total, r_remain, r_time
    
    else:
        try:
            for record in records:
                print(record, 'length is', len(record.data))
                # print("   ", "\n    ".join([record.data[i:i+4].hex() for i in range(0, len(record.data), 4)]))

                if type(record) is UltimakerMaterialRecord:
                    print('     GUID:', record._material_id)
                    print('     version:', record._version)
                    print('     compatibility_version:', record._compatibility_version)
                    print('     serial_number:', record._serial_number)
                    print('     manufacturing_timestamp:', record._manufacturing_timestamp)
                    print('     programming_station_id:', record._programming_station_id)
                    print('     batch_code:', record._batch_code)

                if type(record) is UltimakerStatRecord:
                    print('     version:', record._version)
                    print('     compatibility_version:', record._compatibility_version)
                    print('     material_unit:', record._material_unit, '({})'.format(record._unit))
                    print('     material_total:', record._material_total, record._unit)
                    print('     material_remaining:', record._material_remaining, record._unit)
                    print('     total_usage_duration:', int(record._total_usage_duration/3600), 'h')
        except:
            print('Tag contains no records. Is it a blank tag perhaps?')

def cmd_read_page(start, count=4):
    return [0xff, 0xb0, (start >> 8) & 0xff, start & 0xff, count & 0xff]

def cmd_write_page(start, data):
    if isinstance(data, bytes):
        data = list(data)
    count = len(data)
    return [0xff, 0xd6, (start >> 8) & 0xff, start & 0xff, count & 0xff] + data

def availableReaders():
    return len(readers())

def writeSpool(id, unit, tw, ui=False):
    service = None
    try:
        print('Waiting for tag...')
        service = request.waitforcard()
    except CardRequestTimeoutException:
        print('No card detected after ', TIMEOUT, ' seconds. Aborting read.')
        if ui:
            return None, None # The ui will interpret this as no card.

    try:
        # Connect to card
        connection = service.connection
        connection.connect()
        print('Connected to NFC Tag. ATR Response = {}'.format(util.toHexString(connection.getATR())))
        
        # Get card UID
        uid_data, sw1, sw2 = connection.transmit(get_uid)
        uid = util.toHexString(uid_data)
        status = util.toHexString([sw1, sw2])
        serial = hexlify(bytes(uid_data)).decode('latin').upper()
        print('UID = {}\tstatus = {}\tdata={}'.format(uid, status, uid_data))
        
        # Create spool data for this tag
        spool = MyFilamentSpool(uuid.UUID(id), serial, unit, tw)
        decode(spool.data())
        tag_data = spool.data()

        for i in range(0, len(tag_data), 4): # count from 0 to number of pages in steps of 4
            page = i//4 + 4
            data = list(tag_data[i:i+4])  # no padding required, length of encoded data is already a multiple of 4 
            recv, sw1, sw2 = connection.transmit(cmd_write_page(page, data))
            
            if not ui:
                print('[{:02x}] = {}'.format(page, util.toHexString(data)))
                print('[{:02x}] = {}\trecv = {}\tstatus = {}'.format(page, util.toHexString(data),
                                                                 util.toHexString(recv),
                                                                 util.toHexString([sw1, sw2])))
        connection.transmit(beep)
        decode(bytes(tag_data))

    except NoCardException:
        print('ERROR: Card was removed')

def readSpool(ui=False):
    service = None
    try:
        print('Waiting for tag...')
        service = request.waitforcard()
    except CardRequestTimeoutException:
        print('No card detected after ', TIMEOUT, ' seconds. Aborting read.')
        if ui:
            return None, None, None, None, None, None # The ui will interpret this as no card.
    
    try:
        # Connect to card
        connection = service.connection
        connection.connect()
        print('Connected to NFC Tag. ATR Response = {}'.format(util.toHexString(connection.getATR())))
        
        # Get card UID
        uid_data, sw1, sw2 = connection.transmit(get_uid)
        uid = util.toHexString(uid_data)
        status = util.toHexString([sw1, sw2])
        serial = hexlify(bytes(uid_data)).decode('latin').upper()
        print('UID = {}\tstatus = {}\tdata={}'.format(uid, status, uid_data))

        data = list()
        tagDataLength = 300 # Ultimaker doesn't write past ~225 anyway so read to 300
        for i in range(0, tagDataLength, 4):
            page = i//4 + 4
            pdata, sw1, sw2 = connection.transmit(cmd_read_page(page))
            if not ui:
                print('[{:02x}] = {}\tstatus = {}'.format(page, util.toHexString(pdata), util.toHexString([sw1, sw2])))
            data.append(pdata)

        tag_data = [item for sublist in data for item in sublist]

    except (NoCardException, IndexError):
        print('ERROR: Card was removed')
        if ui:
            return 2, DEFAULT_SERIAL, 0, 0, 0, 0
    
    if ui:
        cardStatus, r_guid, r_total, r_remain, r_time = decode(bytes(tag_data), ui=True)
        return cardStatus, serial, r_guid, r_total, r_remain, r_time
    else:
        decode(bytes(tag_data))

def save_bin(material:MyFilamentSpool, fbin:str='spool.bin'):
    with open(fbin, 'wb') as f:
        f.write(material.data())

def load_bin(file:str):
    with open(file, 'rb') as b:
        decode(b.read())



# /---------------------------------\
#|      Create Smartcard Objects     |
# \---------------------------------/
card_type = AnyCardType()
request = CardRequest(timeout=TIMEOUT, cardType=card_type)



# /---------------------------------\
#|           CL Spool Maker          |
# \---------------------------------/
if __name__ == '__main__':

    ### Custom Command Line Spool Maker ###
    '''--Material GUID--:     '''
    guid = 'e92c7723-0763-4cb7-9864-562dce715c9e'
    
    '''--Material Unit--:     '''
    mu = 2#mg
    
    '''--Material Weight--:   '''
    total_weight = 1000000#mg
    
    # Write spool
    print('Trying to read tag...')
    writeSpool(guid, mu, total_weight)
    print('Operation completed :)')

#!/usr/bin/env python3

from __future__ import print_function

import math
import ctypes
import binascii
import crcmod

def assert_eq(a, b):
    if isinstance(a, ctypes.Array):
        assert_eq(a._type_, b._type_)
        assert_eq(a._length_, b._length_)
        assert_eq(a[:], b[:])
        return

    assert a == b, "%s (%r) != %s (%r)" % (a, a, b, b)

def return_fill_buffer(b, value):
    return (b._type_ * b._length_)(*([value] * b._length_))

def print_struct(s, indent=''):
    for field_name, field_type in s._fields_:
        field_detail = getattr(s.__class__, field_name)
        field_value = getattr(s, field_name)
        print(indent, field_name, end=': ', sep='')
        if isinstance(field_value, ctypes.Structure):
            print()
            print_struct(field_value, indent=indent+'    ')
        elif isinstance(field_value, ctypes.Array):
            print(field_value._length_, field_value[:])
        elif isinstance(field_value, bytes):
            print(repr(field_value))
        else:
            print(hex(field_value))


class Voltage(ctypes.LittleEndianStructure):
    """
    >>> print(Voltage.create(5.0))
    5V0
    >>> print(Voltage.create(3.3))
    3V3
    >>> print(Voltage.create(2.5))
    2V5
    >>> print(Voltage.create(1.8))
    1V8
    >>> print(Voltage.create(1.5))
    1V5
    >>> print(Voltage.create(1.2))
    1V2
    >>> print(Voltage.create(1.0))
    1V0
    >>> print(Voltage.create(0.9))
    0V9
    """
    _pack_ = 1
    _fields_ = [
         ("ones", ctypes.c_uint8, 4),
         ("tenths", ctypes.c_uint8, 4),
    ]

    @staticmethod
    def create(value):
        ones = int(math.floor(value))
        tenths = int(round((value - ones) * 10))
        return Voltage(ones, tenths)

    def __str__(self):
        return "%iV%i" % (self.ones, self.tenths)


class Voltage(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
         ("ones", ctypes.c_uint8, 6),
         ("tenths", ctypes.c_uint8, 2),
    ]
    """
    >>> print(Speed.create(1500))
    1G5
    >>> print(Speed.create(3125))
    3G2
    >>> print(Speed.create(5000))
    5G0
    >>> print(Speed.create(6000))
    6G0
    >>> print(Speed.create(8000))
    8G0
    >>> print(Speed.create(14000))
    14G0
    >>> print(Speed.create(16000))
    16G0
    >>> print(Speed.create(28000))
    28G0
    >>> print(Speed.create(56000))
    56G0
    """

    @staticmethod
    def create(value):
        value = value / 1000
        ones = int(math.floor(value))
        tenths = int(round((value - ones) * 10))
        return Voltage(ones, tenths)

    def __str__(self):
        return "%iG%i" % (self.ones, self.tenths)


'''

class TOFE_Connector_Pin(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
    


class TOFE_EEPROM(ctypes.LittleEndianStructure):
    """Structure representing the TOFE EEPROM format.
    """

    _pack_ = 1
    _fields_ = [
        ("magic", ctypes.c_char * 4),
        ("tofe_version", ctypes.c_uint16),
        ("tofe_crc8_data", ctypes.c_byte),
        ("tofe_crc8_full", ctypes.c_byte),
        # Board information
        ("vendor", ctypes.c_byte * 16),
        ("product", ctypes.c_byte * 14),
        ("product_version", ctypes.c_uint16),
        ("serialno", ctypes.c_byte * 16),
        # Connector information
        ("connector_size", ctypes.c_uint8),

        ("crc8_data", ctypes.c_uint8),
        ("crc8_full", ctypes.c_uint8),
        # Microchip section
        ("wp_empty", ctypes.c_byte * 120),
        ("wp_mac", ctypes.c_byte * 8),
    ]

    DEF_MAGIC = b'TOFE'
    DEF_RMAGIC = b'EOFE'

    def populate(self):
        self.fx2.populate()
        self.sep_start = b'\0'
        self.magic = self.DEF_MAGIC
        self.version = 1
        self.sep_start = b'\0'
        self.sep_end = b'\0'
        self.rmagic = self.DEF_RMAGIC

        self.eventlog_size = 0
        self.eventlog_data = return_fill_buffer(self.eventlog_data, 0)

        self.pcb_pad = return_fill_buffer(self.pcb_pad, 0)
        self.wp_empty = return_fill_buffer(self.wp_empty, 0xff)
        if self.wp_mac[0] == 0:
             self.wp_mac[0] = -1
             self.wp_mac[1] = -1

        self.crc8_data = self.calculate_crc_data()
        self.crc8_full = self.calculate_crc_full()

    def check(self):
        self.fx2.check()
        assert_eq(self.sep_start, b'\0')
        assert_eq(self.magic, self.DEF_MAGIC)
        assert_eq(self.version, 1)
        assert_eq(self.rmagic, self.DEF_RMAGIC)
        assert_eq(self.sep_end, b'\0')

        assert_eq(self.pcb_pad, return_fill_buffer(self.pcb_pad, 0))
        assert_eq(self.wp_empty, return_fill_buffer(self.wp_empty, 0xff))

        assert_eq(self.crc8_data, self.calculate_crc_data())
        assert_eq(self.crc8_full, self.calculate_crc_full())

    def as_bytearray(self):
        return bytearray((ctypes.c_byte * 256).from_address(ctypes.addressof(self)))

    def data_bytes(self):
        raw_bytes = self.as_bytearray()
        return raw_bytes[self.__class__.sep_start.offset+1:self.__class__.sep_end.offset]

    def calculate_crc_data(self):
        import crcmod
        data_crc = crcmod.predefined.Crc('crc-8')
        data_crc.update(self.data_bytes())
        return data_crc.crcValue

    def full_bytes(self):
        raw_bytes = self.as_bytearray()
        return raw_bytes[0:self.__class__.crc8_data.offset] + raw_bytes[self.__class__.crc8_full.offset+1:]

    def calculate_crc_full(self):
        full_crc = crcmod.predefined.Crc('crc-8')
        full_crc.update(self.full_bytes())
        return full_crc.crcValue

    @classmethod
    def size(cls):
        return ctypes.sizeof(OpsisEEPROM)

    def pcb_commit_set(self, sha1):
        self.pcb_commit = (ctypes.c_byte * 20)(*binascii.unhexlify(sha1))

    def pcb_commit_get(self):
        return binascii.hexlify(bytes(self.pcb_commit))

    def eui48(self):
        assert self.wp_mac[0] == -1
        assert self.wp_mac[1] == -1
        assert self.wp_mac[2] == 0
        return list((x & 0xff,) for x in self.wp_mac[2:])

    def mac(self):
        return ":".join("%02x" % x for x in self.eui48())

    def mac_barcode(self):
        import barcode
        return barcode.get('Code128', self.mac())

    def eui64(self):
        if self.wp_mac[0] == 0:
            mac = list(self.wp_mac)
        else:
            assert self.wp_mac[0] == -1
            assert self.wp_mac[1] == -1
            assert self.wp_mac[2] == 0
            mac = self.wp_mac[2:4] + [0xff, 0xfe] + self.wp_mac[5:]

        return "".join("%02x" % (x & 0xff,) for x in mac)

assert_eq(ctypes.sizeof(OpsisEEPROM), 256)
assert_eq(OpsisEEPROM.size(), 256)

if __name__ == "__main__":
    e = OpsisEEPROM()
    print_struct(e)
    print(e.as_bytearray())
    e.populate()
    print_struct(e)
    print(e.as_bytearray())
    e.check()
    import time
    e.prod_program = int(time.time())

    print("Data bytes:", e.data_bytes())
    try:
        assert_eq(e.crc8_data, e.calculate_crc_data())
        raise SystemError("CRC Check didn't fail!")
    except AssertionError:
        pass
    e.crc8_data = e.calculate_crc_data()
    assert_eq(e.crc8_data, e.calculate_crc_data())

    print("Full bytes:", e.full_bytes())
    try:
        assert_eq(e.crc8_full, e.calculate_crc_full())
        raise SystemError("CRC Check didn't fail!")
    except AssertionError:
        pass
    e.crc8_full = e.calculate_crc_full()
    assert_eq(e.crc8_full, e.calculate_crc_full())

    e.check()

    e.wp_mac[0] = -1
    e.wp_mac[1] = -1
    e.wp_mac[2] = 0
    e.wp_mac[3] = 0x12
    e.wp_mac[4] = 0x34
    e.wp_mac[5] = 0x56
    e.wp_mac[6] = 0x78
    e.wp_mac[7] = 0x9a
    e.mac_barcode().save('barcode_mac', {'module_height': 7, 'font_size': 12, 'text_distance': 5, 'human': 'MAC - %s' % e.mac()})
'''

if __name__ == "__main__":
    import doctest
    doctest.testmod()

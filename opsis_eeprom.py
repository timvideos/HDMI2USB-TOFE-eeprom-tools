#!/usr/bin/env python3

from __future__ import print_function

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

class FX2C0Config(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("format", ctypes.c_uint8),
        ("vid", ctypes.c_uint16),
        ("pid", ctypes.c_uint16),
        ("did", ctypes.c_uint16),
        ("config", ctypes.c_uint8),
    ]

    FORMAT_FX2_C0 = 0xC0
    VID_NUMATO = 0x2A19
    PID_OPSIS_UNCONFIG = 0x5440

    def populate(self):
        self.format = self.FORMAT_FX2_C0
        self.vid = self.VID_NUMATO
        self.pid = self.PID_OPSIS_UNCONFIG

    def check(self):
        assert_eq(self.format, self.FORMAT_FX2_C0)
        assert_eq(self.vid, self.VID_NUMATO)
        assert_eq(self.pid, self.PID_OPSIS_UNCONFIG)


class OpsisEEPROM(ctypes.LittleEndianStructure):
    """Structure representing the Opsis EEPROM format.
    """

    _pack_ = 1
    _fields_ = [
        ("fx2", FX2C0Config),
        # Format information
        ("sep_start", ctypes.c_char),
        ("magic", ctypes.c_char * 5),
        ("version", ctypes.c_uint16),
        # PCB information
        ("pcb_batch", ctypes.c_uint64),
        ("pcb_commit", ctypes.c_byte * 20),
        ("pcb_pad", ctypes.c_byte * 4),
        # Production information
        ("prod_batch", ctypes.c_uint64),
        ("prod_program", ctypes.c_uint64),
        # Event Log
        ("eventlog_size", ctypes.c_uint8),
        ("eventlog_data", ctypes.c_byte * 55),
        # Checksum
        ("rmagic", ctypes.c_char * 5),
        ("sep_end", ctypes.c_char),
        ("crc8_data", ctypes.c_uint8),
        ("crc8_full", ctypes.c_uint8),
        # Microchip section
        ("wp_empty", ctypes.c_byte * 120),
        ("wp_mac", ctypes.c_byte * 8),
    ]

    DEF_MAGIC = b'OPSIS'
    DEF_RMAGIC = b'SISPO'

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

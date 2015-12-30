#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 et sts=4 ai:

from __future__ import print_function

import binascii
import crcmod
import ctypes
import time

from utils import *
from tofe_eeprom import *
from fx2_eeprom import *

ATOMS_SPACE = (128 - len(microboot_cfg.buffer) - 1)

class OpsisAtoms(AtomCommon):
    MAGIC = b''
    RAGIC = b''
    magic = b''

    _fields_ = [
        ("version", ctypes.c_uint8),    # 1 byte     1
        ("atoms",   ctypes.c_uint8),    # 1 byte     2
        ("crc8", ctypes.c_ubyte),       # 1 byte     3
        ("_len", ctypes.c_uint8),       # 1 byte     4
        ("_data", ctypes.c_ubyte * (ATOMS_SPACE - 4)),
    ]

    def populate(self):
        AtomCommon.populate(self)
        # Board ID
        #self.add_atom(AtomManufacturerID.create("numato.com"))
        self.add_atom(AtomProductID.create("opsis.h2u.tv"))
        # PCB Information
        self.add_atom(AtomPCBRepository.create(0, "r/pcb.git"))
        self.add_atom(AtomPCBRevision.create("6a18b19"))
        self.add_atom(AtomPCBLicense.create(AtomPCBLicense.Names.CC_BY_SA_v40))
        #self.add_atom(AtomPCBProductionBatchID.create(time.time()))
        #self.add_atom(AtomPCBPopulationBatchID.create(time.time()))
        # EEPROM Information
        #self.add_atom(AtomEEPROMTotalSize.create(0, 256))  # EEPROM is 256 bytes / 2048 bits in size
        #self.add_atom(AtomEEPROMVendorData.create(0, 8))   # FX2 Config bytes
        self.add_atom(AtomEEPROMGUID.create(0xf8, 8))      # MAC address
        #self.add_atom(AtomEEPROMHole.create(0x80, 120))    # Section which returns 0xff
        # Further Repos
        #self.add_atom(AtomSampleCodeRepository.create(1, "r/sample.git"))
        #self.add_atom(AtomDocumentationSite.create(1, ""))

    def leftover(self):
        return ctypes.sizeof(self._data) - self._len


class OpsisEEPROM(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        # FX2 Header
        ("_microboot_cfg", ctypes.c_byte * len(microboot_cfg.buffer)),
        # Info Atoms Data
        ("_atoms", ctypes.c_ubyte * ATOMS_SPACE),
        # Extra Checksum
        ("crc8_full", ctypes.c_uint8),
        # Microchip section
        ("wp_empty", ctypes.c_byte * 120),
        ("wp_mac", ctypes.c_byte * 8),
    ]

    @property
    def microboot(self):
        return FX2Config.from_address(ctypes.addressof(self._microboot_cfg))

    @property
    def atoms(self):
        return OpsisAtoms.from_address(ctypes.addressof(self)+self.__class__._atoms.offset)

    def populate(self):
        self._microboot_cfg[:] = microboot_cfg.buffer[:]

        self.wp_empty = return_fill_buffer(self.wp_empty, 0xff)
        if self.wp_mac[0] == 0:
             self.wp_mac[0] = -1
             self.wp_mac[1] = -1

        self._atoms = return_fill_buffer(self._atoms, 0)
        self.atoms.populate()
        self.crc8_full = self.calculate_crc_full()

    def check(self):
        self.microboot.check()
        self.atoms.crc_check()

        assert_eq(self.wp_empty, return_fill_buffer(self.wp_empty, 0xff))
        assert_eq(self.crc8_full, self.calculate_crc_full())

    def as_bytearray(self):
        return bytearray((ctypes.c_byte * 256).from_address(ctypes.addressof(self)))

    def full_bytes(self):
        raw_bytes = self.as_bytearray()
        return raw_bytes[0:self.__class__.crc8_full.offset] + raw_bytes[self.__class__.crc8_full.offset+1:]

    def calculate_crc_full(self):
        full_crc = crcmod.predefined.Crc('crc-8')
        full_crc.update(self.full_bytes())
        return full_crc.crcValue

    @classmethod
    def size(cls):
        return ctypes.sizeof(OpsisEEPROM)

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

    def __repr__(self):
        s = self.__class__.__name__ + "\n"
        s += "  " + repr(self.microboot) + "\n"
        for seg in self.microboot.segments():
            s += "  " + repr(seg) + "\n"

        s += print_struct(self, indent='  ') + "\n"

        e = self.atoms
        s += "  atoms (%i):\n" % (e.atoms)
        for i in range(0, e.atoms):
            s += "    (%i, %r)\n" % (i, e.get_atom(i))
        return s[:-1]

assert_eq(ctypes.sizeof(OpsisEEPROM), 256)
assert_eq(OpsisEEPROM.size(), 256)


if __name__ == "__main__":
    print("Atom Space:", ATOMS_SPACE)

    e = OpsisEEPROM()
    print(e.as_bytearray())
    e.populate()
    print(e.as_bytearray())
    print(repr(e))
    print("Left:", e.atoms.leftover())
    e.check()

    try:
        e.atoms.add_atom(AtomManufacturerID.create("a"))
        assert_eq(e.crc8_full, e.calculate_crc_full())
        raise SystemError("CRC Check didn't fail!")
    except AssertionError:
        pass
    e.crc8_full = e.calculate_crc_full()
    assert_eq(e.crc8_full, e.calculate_crc_full())

    print(e.as_bytearray())
    print(repr(e))
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

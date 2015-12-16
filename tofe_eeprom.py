#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 et sts=4 ai:

from __future__ import print_function

import re
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


class DynamicLengthStructure(ctypes.LittleEndianStructure):
    r"""
    >>> class Test(DynamicLengthStructure):
    ...    _fields_ = [
    ...        ("b1",      ctypes.c_uint8),
    ...        ("crc8",    ctypes.c_uint8),
    ...        ("_len",    ctypes.c_uint8),
    ...        ("_data",   ctypes.c_ubyte * 0),
    ...    ]
    >>> assert ctypes.sizeof(Test) == 3

    >>> t1 = Test()
    >>> ctypes.sizeof(t1)
    3
    >>> t1._extra_size
    0
    >>> t1.b1
    0
    >>> t1.crc8
    0
    >>> t1.len
    0
    >>> t1._len
    0
    >>> t1.data[:]
    []
    >>> type(t1.data)
    <class '__main__.c_ubyte_Array_0'>
    >>> ctypes.sizeof(t1.data)
    0
    >>> t1.as_bytearray()
    bytearray(b'\x00\x00\x00')
    >>> # Changing normal value
    >>> t1.b1 = 0xa
    >>> t1.b1
    10
    >>> t1.as_bytearray()
    bytearray(b'\n\x00\x00')
    >>> # Increasing data length
    >>> t1.len = 1
    >>> ctypes.sizeof(t1)
    4
    >>> t1.data[:]
    [0]
    >>> type(t1.data)
    <class '__main__.c_ubyte_Array_1'>
    >>> ctypes.sizeof(t1.data)
    1
    >>> t1.as_bytearray()
    bytearray(b'\n\x00\x01\x00')
    >>> t1.data[0] = 0xf
    >>> t1.data[:]
    [15]
    >>> t1.as_bytearray()
    bytearray(b'\n\x00\x01\x0f')
    >>> # Increasing data length further
    >>> t1.len = 2
    >>> ctypes.sizeof(t1)
    5
    >>> t1.data[:]
    [15, 0]
    >>> t1.as_bytearray()
    bytearray(b'\n\x00\x02\x0f\x00')
    >>> t1.data[1] = 0xe
    >>> t1.data[:]
    [15, 14]
    >>> t1.as_bytearray()
    bytearray(b'\n\x00\x02\x0f\x0e')

    >>> # Test CRC calculation
    >>> t2 = Test()
    >>> # CRC doesn't change on CRC value
    >>> hex(t2.crc_calculate())
    '0x0'
    >>> t2.crc8 = 0xa
    >>> t2.crc8
    10
    >>> hex(t2.crc_calculate())
    '0x0'
    >>> # CRC changes on changing b1
    >>> t2.b1 = 1
    >>> t2.b1
    1
    >>> hex(t2.crc_calculate())
    '0x15'
    >>> # CRC changes on changing values in the data section
    >>> t2.len = 1
    >>> hex(t2.crc_calculate())
    '0x7e'
    >>> t2.data[0] = 1
    >>> hex(t2.crc_calculate())
    '0x79'
    >>> t2.crc_check()
    False
    >>> t2.crc_update()
    >>> hex(t2.crc8)
    '0x79'
    >>> t2.crc_check()
    True

    >>> class TestExtra(DynamicLengthStructure):
    ...    _fields_ = [
    ...        ("b1",      ctypes.c_uint8),
    ...        ("crc8",    ctypes.c_uint8),
    ...        ("_len",    ctypes.c_uint8),
    ...        ("b2",      ctypes.c_uint8),
    ...        ("_data",   ctypes.c_ubyte * 0),
    ...    ]
    >>> assert ctypes.sizeof(TestExtra) == 4
    >>> t3 = TestExtra()
    >>> ctypes.sizeof(t3)
    4
    >>> t3._extra_size
    1
    >>> t3.len
    0
    >>> t3._len
    1
    >>> t3.b2 = 0xf
    >>> t3.as_bytearray()
    bytearray(b'\x00\x00\x01\x0f')
    >>> t3.data[:]
    []
    >>> type(t3.data)
    <class '__main__.c_ubyte_Array_0'>
    >>> ctypes.sizeof(t3.data)
    0
    >>> t3.len = 1
    >>> ctypes.sizeof(t3)
    5
    >>> t3.data[:]
    [0]
    >>> type(t3.data)
    <class '__main__.c_ubyte_Array_1'>
    >>> ctypes.sizeof(t3.data)
    1
    >>> t3.as_bytearray()
    bytearray(b'\x00\x00\x02\x0f\x00')
    >>> t3.data[0] = 0xe
    >>> t3.data[:]
    [14]
    >>> t3.as_bytearray()
    bytearray(b'\x00\x00\x02\x0f\x0e')
    """
    _pack_ = 1

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._len = self._extra_size

    @property
    def _extra_start(self):
        return self.__class__._len.offset+1

    @property
    def _extra_end(self):
        return self.__class__._data.offset

    @property
    def _extra_size(self):
        return self._extra_end - self._extra_start

    @property
    def len(self):
        return self._len - self._extra_size

    @len.setter
    def len(self, value):
        ctypes.resize(self, self._extra_end + value)
        self._len = self._extra_size + value

    @property
    def data(self):
        addr = ctypes.addressof(self)
        return (ctypes.c_ubyte * self.len).from_address(addr+self._extra_end)

    def as_bytearray(self):
        return bytearray((ctypes.c_ubyte * ctypes.sizeof(self)).from_address(ctypes.addressof(self)))

    def crc_calculate(self):
        raw_bytes = self.as_bytearray()
        bytes_before = raw_bytes[0:self.__class__.crc8.offset]
        bytes_after = raw_bytes[self.__class__.crc8.offset+1:]

        crc = crcmod.predefined.Crc('crc-8')
        crc.update(bytes_before)
        crc.update(bytes_after)
        return crc.crcValue

    def crc_check(self):
        return self.crc8 == self.crc_calculate()

    def crc_update(self):
        self.crc8 = self.crc_calculate()
        assert self.crc_check()


class Atom(DynamicLengthStructure):
    TYPE = 0xff
    _fields_ = [
        ("type",    ctypes.c_uint8),
        ("index",   ctypes.c_uint8),
        ("crc8",    ctypes.c_uint8),
        ("_len",    ctypes.c_uint8),
        ("_data",   ctypes.c_ubyte * 0),
    ]

assert ctypes.sizeof(Atom) == 4


class AtomString(Atom):

    @classmethod
    def create(cls, s):
        u"""
        >>> a1 = AtomString.create("numato")
        >>> a1.len
        7
        >>> a1.str
        'numato'
        >>> a1.as_bytearray()
        bytearray(b'\\xff\\xff\\xff\\x07numato\\x00')
        >>> a1.data[:]
        [110, 117, 109, 97, 116, 111, 0]
        >>> a2 = AtomString.create(u"\u2603")
        >>> a2.len
        4
        >>> a2.str
        '☃'
        >>> a2.data[:]
        [226, 152, 131, 0]
        """
        o = cls(type=cls.TYPE, index=0xff, crc8=0xff)
        assert o.type == cls.TYPE
        assert o.index == 0xff
        assert o.crc8 == 0xff
        assert o._len == 0
        o.str = s
        return o

    @property
    def str(self):
        return bytearray(self.data[:-1]).decode('utf-8')

    @str.setter
    def str(self, s):
        b = s.encode('utf-8')
        self.len = len(b)+1
        self.data[:-1] = b[:]
        self.data[-1] = 0x0


AtomURL = AtomString

class AtomRepo(Atom):
    class AtomRepoContains(ctypes.LittleEndianStructure):
        _pack_ = 1
        _fields_ = [
             ("vendor", ctypes.c_uint8, 1),
             ("reserved", ctypes.c_uint8, 3),
             ("sample_code", ctypes.c_uint8, 1),
             ("docs", ctypes.c_uint8, 1),
             ("firmware", ctypes.c_uint8, 1),
             ("pcb", ctypes.c_uint8, 1),
        ]

    assert ctypes.sizeof(AtomRepoContains) == 1

    _fields_ = [
        ("contains", AtomRepoContains),
        ("revtype", ctypes.c_uint8),
        ("_data", ctypes.c_char * 0),
    ]

    @classmethod
    def create(cls, contains, url, rev):
        r"""
        >>> r = AtomRepo.create(["pcb"], "github.com/timvideos/abc.git", "g480cd42")
        >>> r.contains.vendor
        0
        >>> r.contains.pcb
        1
        >>> r.url
        'github.com/timvideos/abc.git'
        >>> r.rev
        'g480cd42'
        >>> r.as_bytearray()
        bytearray(b'\xff\xff\xff(\x80\x00github.com/timvideos/abc.git\x00g480cd42\x00')
        """
        c = AtomRepo.AtomRepoContains()
        for name in contains:
            setattr(c, name, True)

        o = cls(type=cls.TYPE, index=0xff, crc8=0xff)
        assert o.type == cls.TYPE
        assert o.index == 0xff
        assert o.crc8 == 0xff
        #assert o._len == 1
        o.contains = c
        o.set_urlrev(url, rev)
        return o

    def _find_first_null(self):
        for i, d in enumerate(self.data):
            if d == 0:
                return i

    @property
    def url(self):
        return bytearray(self.data[0:self._find_first_null()]).decode('utf-8')

    @url.setter
    def url(self, value):
        self.set_urlrev(value, self.rev)

    @property
    def rev(self):
        return bytearray(self.data[self._find_first_null()+1:-1]).decode('utf-8')

    @rev.setter
    def rev(self, value):
        self.set_urlrev(self.url, value)

    def set_urlrev(self, url, rev):
        raw_url = url.encode('utf-8')
        raw_rev = rev.encode('utf-8')

        a1 = 0
        a2 = a1 + len(raw_url)
        b1 = a2+1
        b2 = b1 + len(raw_rev)

        self.len = b2 - a1 + 1
        self.data[a1:a2] = raw_url
        self.data[a2] = 0x0
        self.data[b1:b2] = raw_rev
        self.data[b2] = 0x0

from enum import Enum

class AtomEEPROMInfo(Atom):
    TYPE = 0x07

    class Types(Enum):
        SIZE = 0x1
        TOFE = 0x2
        USER = 0x3
        GUID = 0x4
        EMPTY = 0x5

    class Small(ctypes.LittleEndianStructure):
        _pack_ = 1
        _fields_ = [
            ("offset", ctypes.c_uint8),
            ("size", ctypes.c_uint8),
        ]

    class Medium(ctypes.LittleEndianStructure):
        _pack_ = 1
        _fields_ = [
            ("offset", ctypes.c_uint16),
            ("size", ctypes.c_uint16),
        ]

    class Large(ctypes.LittleEndianStructure):
        _pack_ = 1
        _fields_ = [
            ("offset", ctypes.c_uint32),
            ("size", ctypes.c_uint32),
        ]

    _fields_ = [
        ("feature", ctypes.c_uint8),
        ("_data", ctypes.c_ubyte * 0),
    ]


    @classmethod
    def create(cls, feature, offset, size):
        r"""
        >>> e = AtomEEPROMInfo.create(AtomEEPROMInfo.Types.SIZE, 5, 10)
        >>> e.len
        2
        >>> e.offset
        5
        >>> e.size
        10
        >>> e.as_bytearray()
        bytearray(b'\x07\xff\xff\x03\x01\x05\n')

        >>> e = AtomEEPROMInfo.create(AtomEEPROMInfo.Types.SIZE, 700, 10)
        >>> e.len
        4
        >>> e.offset
        700
        >>> e.size
        10
        >>> e.as_bytearray()
        bytearray(b'\x07\xff\xff\x05\x01\xbc\x02\n\x00')
        """
        if offset < 2**8 and size < 2**8:
            struct = AtomEEPROMInfo.Small
        elif offset < 2**16 and size < 2**16:
            struct = AtomEEPROMInfo.Medium
        elif offset < 2**32 and size < 2**32:
            struct = AtomEEPROMInfo.Large
        else:
            assert False

        o = cls(type=cls.TYPE, index=0xff, crc8=0xff)
        o.feature = feature.value
        o.len = ctypes.sizeof(struct)
        o.offset = offset
        o.size = size
        return o

    @property
    def _data_struct(self):
        if self.len == ctypes.sizeof(AtomEEPROMInfo.Small):
            return AtomEEPROMInfo.Small.from_address(ctypes.addressof(self.data))
        elif self.len == ctypes.sizeof(AtomEEPROMInfo.Medium):
            return AtomEEPROMInfo.Medium.from_address(ctypes.addressof(self.data))
        elif self.len == ctypes.sizeof(AtomEEPROMInfo.Large):
            return AtomEEPROMInfo.Large.from_address(ctypes.addressof(self.data))
        else:
            assert False

    @property
    def offset(self):
        return self._data_struct.offset

    @offset.setter
    def offset(self, value):
        self._data_struct.offset = value

    @property
    def size(self):
        return self._data_struct.size

    @size.setter
    def size(self, value):
        self._data_struct.size = value


class AtomDesigner(AtomURL):
    TYPE = 0x01

class AtomManufacturer(AtomURL):
    TYPE = 0x02

class AtomProductID(AtomURL):
    TYPE = 0x03

class AtomProductVersion(AtomString):
    TYPE = 0x04

class AtomProductRepo(AtomRepo):
    TYPE = 0x05

class AtomProductSerialNumber(AtomString):
    TYPE = 0x06

class AtomExtraRepo(AtomRepo):
    TYPE = 0x9


class TOFE_EEPROM(DynamicLengthStructure):
    """Structure representing the TOFE EEPROM format.
    """
    _pack_ = 1
    _fields_ = [
        ("magic", ctypes.c_char * 4),
        ("version", ctypes.c_uint8),
        ("atoms", ctypes.c_uint8),
        ("crc8", ctypes.c_ubyte),
        ("_len", ctypes.c_uint32),
        ("_data", ctypes.c_ubyte * 0),
    ]

    def __init__(self):
        super().__init__()
        self.magic = b'TOFE'
        self.version = 0x1
        self.atoms = 0
        self.crc_update()

    @classmethod
    def create(cls, *args, **kw):
        """
        """
        return cls("MAGIC", 0x1, 0, 0xff, 0, '', *args, **kw)

    def add_atom(self, atom):
        atom_size = ctypes.sizeof(atom)

        atom_offset = self.len
        assert atom.index == 0xff, atom.index
        atom.index = self.atoms
        self.atoms += 1
        atom.crc_update()

        self.len += atom_size
        ctypes.memmove(ctypes.addressof(self.data)+atom_offset, ctypes.addressof(atom), atom_size)

        self.crc_update()

    def get_atom(self, i):
        current_offset = 0
        a = None
        for i in range(0, i+1):
            a = Atom.from_address(ctypes.addressof(self.data)+current_offset)
            assert a.index == i, "%i != %i" % (a.index, i)
            current_offset += ctypes.sizeof(Atom)
            current_offset += a.len
        assert a is not None, a
        a.crc_check()
        return a

MilkyMistEEPROM = TOFE_EEPROM()
MilkyMistEEPROM.add_atom(AtomManufacturer.create("numato.com"))
MilkyMistEEPROM.add_atom(AtomProductID.create("tofe.io/milkymist"))
MilkyMistEEPROM.add_atom(AtomProductRepo.create(["pcb", "docs"], "tofe.io/milkymist.git", "aaaaaaa"))

a = MilkyMistEEPROM.as_bytearray()
print(len(a), a)

LowSpeedIOEEPROM = TOFE_EEPROM()
LowSpeedIOEEPROM.add_atom(AtomManufacturer.create("numato.com"))
LowSpeedIOEEPROM.add_atom(AtomProductID.create("tofe.io/lowspeedio"))
LowSpeedIOEEPROM.add_atom(AtomProductRepo.create(["pcb", "docs", "firmware"], "tofe.io/lowspeedio.git", "aaaaaaa"))

b = LowSpeedIOEEPROM.as_bytearray()
print(len(b), b)


Opsis = TOFE_EEPROM()
Opsis.add_atom(AtomManufacturer.create("numato.com"))
Opsis.add_atom(AtomProductID.create("opsis.h2u.tv"))
Opsis.add_atom(AtomProductRepo.create(["pcb"], "r/pcb.git", "aaaaaaa"))
Opsis.add_atom(AtomProductRepo.create(["sample_code"], "r/sample.git", ""))
Opsis.add_atom(AtomProductRepo.create(["docs"], "r/docs.git", ""))
Opsis.add_atom(AtomEEPROMInfo.create(AtomEEPROMInfo.Types.SIZE, 0, 256))
Opsis.add_atom(AtomEEPROMInfo.create(AtomEEPROMInfo.Types.GUID, 0xf8, 8))
Opsis.add_atom(AtomEEPROMInfo.create(AtomEEPROMInfo.Types.EMPTY, 0x80, 120))

b = Opsis.as_bytearray()
print(len(b), b)

if __name__ == "__main__":
    import doctest
    doctest.testmod()

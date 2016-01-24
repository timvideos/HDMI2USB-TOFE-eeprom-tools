#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 et sts=4 ai:

# LowSpeedIO EEPROM
# ------------------------------------------------
lowspeedio_eeprom = TOFEAtoms()
lowspeedio_eeprom.add_atom(AtomManufacturerID.create("numato.com"))         # 1
lowspeedio_eeprom.add_atom(AtomProductID.create("tofe.io/lowspeedio"))      # 2
lowspeedio_eeprom.add_atom(AtomProductVersion.create("v1.0.0"))             # 3
lowspeedio_eeprom.add_atom(AtomPCBRepository.create(1, "r/pcb.git"))        # 4
lowspeedio_eeprom.add_atom(AtomPCBRevision.create("18b01dd"))               # 5
lowspeedio_eeprom.add_atom(AtomPCBLicense.create(AtomPCBLicense.Names.CC_BY_SA_v40)) # 6
lowspeedio_eeprom.add_atom(AtomEEPROMTotalSize.create(0, 16*1024))          # 7
lowspeedio_eeprom.add_atom(AtomEEPROMVendorData.create(0x600, 256))         # 8
lowspeedio_eeprom.add_atom(AtomEEPROMVendorData.create(0x800, 2))           # 9
lowspeedio_eeprom.add_atom(AtomEEPROMTOFEData.create(0, 1024))              # 10
lowspeedio_eeprom.add_atom(AtomEEPROMUserData.create(0x400, 256))           # 11
lowspeedio_eeprom.add_atom(AtomEEPROMPartNumber.create("PIC18F14K50"))      # 12
lowspeedio_eeprom.add_atom(AtomEEPROMGUIDWrite.create(0x700, 16))           # 13
lowspeedio_eeprom.add_atom(AtomComment.create("Thanks for backing!"))       # 14
lowspeedio_eeprom.add_atom(AtomCommentOn.create(8, """\
ADC Values - 0x6XY
X == Channel (0->5)
Y == 0 - Enable/Disable
Y == 1 - Update counter
Y == 2 - ADC Value (Low Byte)
Y == 3 - ADC Value (High Byte)
"""))
    lowspeedio_eeprom.add_atom(AtomCommentOn.create(9, """\
LED Control
0x800 - D5
0x801 - D6
"""))

b = lowspeedio_eeprom.as_bytearray()
print("-"*10)
print("LowSpeedIO")
print(len(b), b)
print("/*")
print(repr(lowspeedio_eeprom))
print("*/")
l = []
s = []
for d in b:
    s.append('0x%02x' % d)
    if len(s) == 16:
        l.append(", ".join(s))
        s = []
l.append(", ".join(s))
print("const rom uint8_t _veeprom_flash_data[] = {")
print("   ",",\n    ".join(l))
print("};")

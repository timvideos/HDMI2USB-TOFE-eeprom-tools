#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 et sts=4 ai:

from tofe_eeprom import TOFEAtoms

# MilkyMist EEPROM
# ------------------------------------------------
milkymist_eeprom = TOFEAtoms()
milkymist_eeprom.add_atom(AtomManufacturerID.create("numato.com"))
milkymist_eeprom.add_atom(AtomProductID.create("tofe.io/milkymist"))
milkymist_eeprom.add_atom(AtomProductVersion.create("v1.0.0"))
milkymist_eeprom.add_atom(AtomPCBRepository.create(1, "r/pcb.git"))
milkymist_eeprom.add_atom(AtomPCBRevision.create("a902c70"))
milkymist_eeprom.add_atom(AtomPCBLicense.create(AtomPCBLicense.Names.CC_BY_SA_v40))
milkymist_eeprom.add_atom(AtomPCBProductionBatchID.create(1450787283)) # time.time()))
milkymist_eeprom.add_atom(AtomEEPROMTotalSize.create(0, 128))
milkymist_eeprom.add_atom(AtomEEPROMPartNumber.create("24LC01BT-1/OT"))
milkymist_eeprom.add_atom(AtomComment.create("Thanks for backing!"))
milkymist_eeprom.crc_check()

b = milkymist_eeprom.as_bytearray()
print("-"*10)
print("MilkyMist")
print(len(b), b)
print(repr(milkymist_eeprom))
f = open("milkymist_eeprom.bit", "bw")
f.write(b)
f.close()

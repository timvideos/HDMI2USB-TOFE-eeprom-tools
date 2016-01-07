"""
#   Name           Identifier-name,         Poly            Reverse         Init-value      XOR-out     Check
[   'crc-8',            'Crc8',             0x107,          NON_REVERSE,    0x00,           0x00,       0xF4,       ],
"""
from io import StringIO
from crcmod import Crc
c8 = 0x107
code = StringIO()
Crc(c8, rev=False).generateCode('crc8',code)

out = open('opsis_eeprom_crc.c', 'w')
out.write(code.getvalue().replace('UINT8', '__u8'))
out.close()




import subprocess
import barcode
from barcode.writer import ImageWriter

# Needs to be 2.8 inch by 0.850 inch at 300dpi
# 2.800 * 300 == 840.0
# 0.850 * 300 == 255.0

m = barcode.get('Code128', "tofe.io/milkymist", writer=ImageWriter())
params = {'module_height': 19.00, 'module_width': 0.29750000000000000, 'font_size': 15, 'text_distance': -2, 'human': ' '}
m.save('barcode-tofe-milkymist', params)
print(840, 255)
subprocess.call("file barcode-tofe-milkymist.png", shell=True)

l = barcode.get('Code128', "tofe.io/lowspeedio", writer=ImageWriter())
params = {'module_height': 19.00, 'module_width': 0.28350000000000000, 'font_size': 15, 'text_distance': -2, 'human': ' '}
l.save('barcode-tofe-lowspeedio', params)
print(840, 255)
subprocess.call("file barcode-tofe-lowspeedio.png", shell=True)

# Needs to be 3.5 inch by 0.500 inch at 300dpi
# 3.500 * 300 == 1050.0
# 0.500 * 300 ==  150.0
params = {'module_height': 10.10, 'module_width': 0.50200000000000000, 'font_size': 15, 'text_distance': -2, 'human': ' '}
o = barcode.get('Code128', "opsis.h2u.tv", writer=ImageWriter())
o.save('barcode-opsis', params)
print(1050.0, 150.0)
subprocess.call("file barcode-opsis.png", shell=True)

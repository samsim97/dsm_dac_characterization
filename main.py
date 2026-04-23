import re
import time

import pyvisa
import numpy as np

from redpitaya.redpitaya import redpitaya

WORD_WIDTH = 20
INITIAL_DIGITAL_VALUE = 0
# INITIAL_DIGITAL_VALUE = -2 ** (WORD_WIDTH - 1)

rm = pyvisa.ResourceManager()
inst = rm.open_resource('GPIB0::16::INSTR')
inst.timeout = 5000
rp = redpitaya()
rp.pin_write_dir(1, 'N', 'OUT')
rp.pin_write(1, 'N', 0)
word_value = INITIAL_DIGITAL_VALUE
filename = f"data_{int(time.time())}.csv"
# print(rm.list_resources())

data = []
pattern = re.compile(r'^([+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?)')
start = time.time()

for i in range(2 ** (WORD_WIDTH - 1)):
    rp.pin_write(1, 'N', 1)
    word_value += 1
    read: str = inst.query('DATA:FRESh?')
    read_voltage = pattern.match(read).group(1) if pattern.match(read) else '0'
    timestamp = time.time() - start
    data.append( [timestamp, word_value, float(read_voltage)])
    if i % 1000 == 0:
        np.savetxt(filename, data, delimiter=',', header='Timestamp,WordValue,Voltage', comments='')
    rp.pin_write(1, 'N', 0)
    time.sleep(0.005)

# np.savetxt(filename, data, delimiter=',', header='Timestamp,WordValue,Voltage', comments='')
inst.close()
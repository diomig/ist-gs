#from lib import pycubed_rfm9x_fsk
import busio
import board
import digitalio
import time
#print(_RH_RF95_REG_00_FIFO)



spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

print('SCK', board.SCK, 'MOSI', board.MOSI, 'MISO', board.MISO)

prompt = ''

while prompt not in ['q', 'quit', 'exit']:
    prompt = input('>>> ')
    buff = bytearray(prompt, 'utf-8')
    spi.write(buff)
    time.sleep(0.001)
    spi.write(bytearray(1))

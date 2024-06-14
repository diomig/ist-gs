import board
import busio
import digitalio

# Create the SPI bus
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Create the chip select (CS) pin
cs = digitalio.DigitalInOut(board.D5)
cs.direction = digitalio.Direction.OUTPUT
cs.value = True

def read_spi(address, num_bytes):
    while not spi.try_lock():
        pass

    try:
        # Configure the SPI bus
        spi.configure(baudrate=1000000, phase=0, polarity=0)

        # Create the command to read from the specified address
        command = bytearray(num_bytes+1)
        command[0] = address

        # Prepare a buffer to read the data into
        read_buffer = bytearray(num_bytes+1)

        # Select the device by setting the CS line low
        cs.value = False

        # Write the command to the device
        #spi.write(command)
        #print('W', command)
        # Read the response from the device
        #spi.readinto(read_buffer)
        #print('R', read_buffer)

        spi.write_readinto(command, read_buffer)
        print('WR', command, '->', read_buffer)
    finally:
        # Deselect the device by setting the CS line high
        cs.value = True

        # Release the SPI lock
        spi.unlock()

    return read_buffer[1:]





print('SCK', board.SCK, 'MOSI', board.MOSI, 'MISO', board.MISO)

prompt = ''

while prompt not in ['q', 'quit', 'exit']:
    prompt = input('>>> ')
    buff = bytearray(prompt, 'utf-8')
    print(read_spi(0x42, 1))





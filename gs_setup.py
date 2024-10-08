"""
Provides individual groundstation actions such as upload a file,
wait for packet, or send a command.
"""

import board
import busio
import digitalio

from lib import pycubed_rfm9x
from lib.configuration import radio_configuration as rf_config

# from shell_utils import bold, normal


def initialize_rfm9x(spi, cs, reset):
    """
    Initialize the radio - uses lib/configuration/radio_configuration
    to configure with defaults
    """

    rfm_device = pycubed_rfm9x.RFM9x(
        spi,
        cs,
        reset,
        rf_config.FREQUENCY,
    )

    # configure to match satellite
    rfm_device.tx_power = rf_config.TX_POWER
    # rfm_device.bitrate = rf_config.BITRATE
    # rfm_device.frequency_deviation = rf_config.FREQUENCY_DEVIATION
    # rfm_device.rx_bandwidth = rf_config.RX_BANDWIDTH
    rfm_device.preamble_length = rf_config.PREAMBLE_LENGTH

    return rfm_device


def initialize_radiohead(tx_device, rx_device=None, rxtx_switch=None):

    rh = pycubed_rfm9x.Radiohead(
        tx_device,
        rx_device=rx_device,
        rxtx_switch=rxtx_switch,
        checksum=rf_config.CHECKSUM,
    )

    rh.ack_delay = rf_config.ACK_DELAY
    rh.ack_wait = rf_config.ACK_WAIT
    rh.receive_timeout = rf_config.RECEIVE_TIMEOUT
    rh.node = rf_config.GROUNDSTATION_ID
    rh.destination = rf_config.SATELLITE_ID

    return rh


def initialize_radio(
    tx_spi, tx_cs, tx_reset, rx_spi=None, rx_cs=None, rx_reset=None, rxtx_switch=None
):
    tx_device = initialize_rfm9x(tx_spi, tx_cs, tx_reset)
    rx_device = None
    if rx_spi and rx_cs and rx_reset:
        rx_device = initialize_rfm9x(rx_spi, rx_cs, rx_reset)

    return initialize_radiohead(tx_device, rx_device=rx_device, rxtx_switch=rxtx_switch)


def init_spi():
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

    cs = digitalio.DigitalInOut(board.CE0)
    reset = digitalio.DigitalInOut(board.D24)

    return spi, cs, reset

import gs_setup as setup
import shell_utils as su


def radio_setup():
    spi, cs, reset = setup.init_spi()
    radio = setup.initialize_rfm9x(spi, cs, reset)
    print("Radio Initialized")

    su.print_radio_configuration(radio)
    return radio


radio = radio_setup()

from typing import Union, Any, Tuple
from .redpitaya_scpi import scpi, SPIMode
# import time


class redpitaya(scpi):
    """Completion of the SCPI class used to access Red Pitaya over an IP
    network. Adds SPI interface support, some UART helper functions, and some
    hardcoded default configurations.
    """
    DEFAULT_CONF: dict[str, dict[str, Any]] = {
        'scpi': {
            'host'   : "169.254.190.203", # found with arp -a on linux
            'port'   : 5000,
            'timeout': None,
        },
        'uart': {
            'speed'  : 115200,
            'bits'   : "CS8",
            'parity' : "NONE",
            'stop'   : 1,
            'timeout': 10
        },
        'spi': {
            'spi_mode': SPIMode.HISL.value, 
            'cs_mode' : "normal",
            'speed'   : 100000,
            'word_len': 8
        }
    }

    def __init__(self):
        """Initializes scpi connection using hard-coded default configurations.
        """
        super().__init__(**self.DEFAULT_CONF['scpi'])
        self.tx_txt('UART:INIT')
        self.uart_set(**self.DEFAULT_CONF['uart'])
        self.tx_txt('SPI:INIT')
        self.spi_set(**self.DEFAULT_CONF['spi'])
        self.pin_names: dict[str, Tuple[int, str]] = {}


    def close(self):
        """Releases used ressources and closes scpi connection."""
        self.tx_txt('SPI:RELEASE')
        self.tx_txt('UART:RELEASE')
        super().close()

    def pin_read_dir(self, n: int, p: str) -> Union[str, None] :
        """Reads the specified digital pin's direction.

        Args:
            n (int): number of the pin, from 0 to 7
            p (str): polarity of the pin, either 'N' or 'P'
        
        Returns:
            (str): 'OUT' or 'IN' 
        """
        self.tx_txt(f"DIG:PIN:DIR? DIO{n}_{p}")
        return self.rx_txt()

    def pin_write_dir(self, n: int, p: str, d: str) -> None :
        """Configures the specified digital pin's direction.

        Args:
            n (int): number of the pin, from 0 to 7
            p (str): polarity of the pin, either 'N' or 'P'
            d (str): direction of the pin, must be 'IN' or 'OUT'
        """
        self.tx_txt(f"DIG:PIN:DIR {d},DIO{n}_{p}")

    def pin_read(self, n: int, p: str) -> int :
        """Reads the specified digital pin.

        Args:
            n (int): number of the pin, from 0 to 7
            p (str): polarity of the pin, either 'N' or 'P'
        
        Returns:
            (int): 0 or 1 if it is the read value, -1 if no value was read
                   (usually happens in case of an invalid pin name) 
        """
        self.tx_txt(f"DIG:PIN? DIO{n}_{p}")
        return {None: -1, '': -1, '0': 0, '1': 1}[self.rx_txt()]

    def pin_write(self, n: int, p: str, v: int) -> None :
        """Change the value of the specified digital pin.

        Args:
            n (int): number of the pin, from 0 to 7
            p (str): polarity of the pin, either 'N' or 'P'
            v (int): value to be written, either 0 or 1
        """
        self.tx_txt(f"DIG:PIN DIO{n}_{p},{int(bool(v))}")

    def pin_name(self, n: int, p: str, name: str) -> None :
        self.pin_names[name] = (n, p)

    def pin_set(self, name: str, v: int) -> None :
        self.pin_write(self.pin_names[name][0], self.pin_names[name][1], v)

    def pin_get(self, name: str) -> int :
        return self.pin_read(self.pin_names[name][0], self.pin_names[name][1])
    
    def pin_set_dir(self, name: str, d: str) -> None :
        self.pin_write_dir(self.pin_names[name][0], self.pin_names[name][1], d)

    def pin_get_dir(self, name: str) -> Union[str, None] :
        return self.pin_read_dir(self.pin_names[name][0], self.pin_names[name][1])

    def spi_transaction(self, data: int) -> Union[int, None]:
        data = data % 256
        self.tx_txt('SPI:MSG:CREATE 1')
        self.tx_txt(f'SPI:MSG0:TX1:RX {data}')  # 0xAA, 0x55, 0x01, 0x02
        self.tx_txt('SPI:PASS')
        self.tx_txt('SPI:MSG0:RX?')
        self.tx_txt('SPI:MSG:DEL')
        return (
            lambda v: None if v in (None, '') else int(v.strip('{}'))
        )(self.rx_txt())

    def spi_set_mode(self, mode: str) -> None:
        self.DEFAULT_CONF['spi']['spi_mode'] = mode
        self.spi_set(**self.DEFAULT_CONF['spi'])

    def spi_set_speed(self, speed: int) -> None:
        self.DEFAULT_CONF['spi']['speed'] = speed
        self.spi_set(**self.DEFAULT_CONF['spi'])

    def spi_loop(self, it: Union[int, None] = None, delay: float = 1) -> None:
        def _loop():
            #time.sleep(delay)
            # print(f"sending: {bin(i)[2:].zfill(8)} | received: {bin(self.spi_transaction(i))[2:].zfill(8)}")
            print(f"sending: {i} | received: {self.spi_transaction(i)}")
        if it == None:
            i=0
            while (True):
                i = (i+1) % 256
                _loop()
        else:
            for i in range(it):
                _loop()

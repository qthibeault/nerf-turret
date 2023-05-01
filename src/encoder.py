from contextlib import contextmanager

from smbus2 import SMBus


class Encoder:
    ADDR = 0x36

    def __init__(self, bus: SMBus):
        self._bus = bus

    @property
    def angle(self) -> float:
        lo_byte = self._bus.read_byte_data(self.ADDR, 0x0d)
        hi_byte = self._bus.read_byte_data(self.ADDR, 0x0c)
        raw_angle = (hi_byte << 8) + lo_byte
        theta = (raw_angle * 360) / 4096
        return theta % 360


class EncoderMultiplexer:
    ADDR = 0x70

    def __init__(self, bus_idx: int = 1):
        self._bus = SMBus(1)

    @contextmanager
    def select(self, idx: int):
        if not 0 <= idx < 8:
            raise ValueError("Only 8 outputs are allowed")

        try:
            self._bus.write_byte(self.ADDR, idx)
            yield Encoder(self._bus)
        finally:
            self._bus.write_byte(self.ADDR, 0)


from time import sleep

from encoder import Encoder
from gpiozero import DigitalOutputDevice, OutputDevice


class Stepper:
    """Control a stepper motor using an A4988 motor driver."""

    def __init__(
        self,
        step_pin: int,
        dir_pin: int,
        encoder: Encoder,
        direction: str = "cw",
        delay: float = 0.001,
        step_deg: float = 1.8,
        offset: float = 0.0,
    ):
        if direction not in ("cw", "ccw"):
            raise ValueError("Only cw and ccw can be provided as directions")

        if direction == "cw":
            init_val = False
        elif direction == "ccw":
            init_val = True

        self._step_pin = DigitalOutputDevice(step_pin, initial_value=False)
        self._dir_pin = OutputDevice(dir_pin, initial_value=init_val)
        self._enc = encoder
        self._dir = direction
        self._delay = delay
        self._step_deg = step_deg
        self._offset = offset

    @property
    def angle(self) -> float:
        return self._enc.angle - self._offset

    @angle.setter
    def angle(self, new_angle: float):
        if new_angle > self.angle:
            self.direction = "cw"
        elif new_angle < self.angle:
            self.direction = "ccw"
        else:
            return

        while abs(self.angle - new_angle) > self._step_deg:
            self.step()

    @property
    def direction(self) -> str:
        return self._dir

    @direction.setter
    def direction(self, new_dir: str) -> None:
        if new_dir in ("cw", "ccw"):
            self._dir = new_dir
        else:
            raise ValueError(f"Unknown direction {new_dir}")

        if new_dir == "cw":
            self._dir_pin.off()
        elif new_dir == "ccw":
            self._dir_pin.on()

    def step(self, n: int = 1) -> None:
        if self._step_pin.value == 1:
            self._step_pin.off()

        for _ in range(n - 1):
            self._step_pin.on()
            sleep(self._delay)
            self._step_pin.off()
            sleep(self._delay)

        self._step_pin.on()

    def close(self):
        self._step_pin.close()
        self._dir_pin.close()


class BaseStepper(Stepper):
    def left(self, n: int = 1):
        self.direction = "ccw"
        self.step(n)

    def right(self, n: int = 1):
        self.direction = "cw"
        self.step(n)


class ElevStepper(Stepper):
    def up(self, n: int = 1):
        self.direction = "ccw"
        self.step(n)

    def down(self, n: int = 1):
        self.direction = "cw"
        self.step(n)

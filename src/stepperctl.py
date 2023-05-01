from __future__ import annotations

from encoder import Encoder
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import Header, Static, Button, Footer
from smbus2 import SMBus
from stepper import ElevStepper, BaseStepper

bus = SMBus(1)
enc = Encoder(bus)


class StepperHeader(Static):
    pass


class AngleDisplay(Static):
    DEFAULT_CSS = """
    AngleDisplay {
        content-align: center middle;
        height: 3;
    }
    """

    angle = reactive(0.0)

    def watch_angle(self) -> None:
        self.update(f"{self.angle:.2f} °")


class Stepper(Static):
    pass


class BaseStepperCtrl(Stepper):
    """Base stepper control widget"""

    BINDINGS = [
        ("left", "rotate_left", "Rotate left"),
        ("right", "rotate_right", "Rotate right"),
    ]
    DEFAULT_CSS = """
    #right {
        dock: right
    }
    """

    stepper = BaseStepper(step_pin=23, dir_pin=24, encoder=enc, offset=279.76)

    def compose(self) -> ComposeResult:
        yield Button("Left", id="left", variant="success")
        yield AngleDisplay()
        yield Button("Right", id="right", variant="error")

    def on_mount(self) -> None:
        self.query_one(AngleDisplay).angle = self.stepper.angle

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "left":
            self.action_rotate_left()
        elif event.button.id == "right":
            self.action_rotate_right()

    def action_rotate_left(self) -> None:
        self.stepper.left()
        self.query_one(AngleDisplay).angle = self.stepper.angle

    def action_rotate_right(self) -> None:
        self.stepper.right()
        self.query_one(AngleDisplay).angle = self.stepper.angle

    def cleanup_stepper(self) -> None:
        self.stepper.close()


class ElevStepperCtrl(Stepper):
    """Elevation stepper control widget"""

    BINDINGS = [
        ("up", "increase_elev", "Increase elevation"),
        ("down", "decrease_elev", "Decrease elevation"),
    ]
    DEFAULT_CSS = """
    #down {
        dock: right
    }
    """

    stepper = ElevStepper(step_pin=27, dir_pin=22, encoder=enc)

    def compose(self) -> ComposeResult:
        yield Button("Up", id="up", variant="success")
        yield AngleDisplay()
        yield Button("Down", id="down", variant="error")

    def on_mount(self) -> None:
        self.query_one(AngleDisplay).angle = self.stepper.angle

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "up":
            self.action_increase_elev()
        elif event.button.id == "down":
            self.action_decrease_elev()

    def action_increase_elev(self) -> None:
        self.stepper.up()
        self.query_one(AngleDisplay).angle = self.stepper.angle

    def action_decrease_elev(self) -> None:
        self.stepper.down()
        self.query_one(AngleDisplay).angle = self.stepper.angle

    def cleanup_stepper(self):
        self.stepper.close()


class StepperCtrl(App):
    BINDINGS = [
        ("q", "exit_app", "Exit application"),
        ("z", "set_zeros", "Set current angles as zero"),
    ]
    CSS = """
    Stepper {
        layout: horizontal;
        background: $boost;
        height: 5;
        margin: 1;
        min-width: 50;
        padding: 1;
    }

    Stepper > Button {
        width: 16
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield StepperHeader("Base")
        yield BaseStepperCtrl()
        # yield StepperHeader("Elevation")
        # yield ElevStepperCtrl()
        yield Footer()

    def action_exit_app(self) -> None:
        self.query_one(BaseStepperCtrl).cleanup_stepper()
        # self.query_one(ElevStepperCtrl).cleanup_stepper()
        self.exit(None)

    def action_set_zeros(self) -> None:
        pass


if __name__ == "__main__":
    app = StepperCtrl()
    app.run()

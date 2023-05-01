import dataclasses as dc
import socket
import logging
import time

import click
import encoder
import gpiozero
import smbus2
import stepper
import turret_client.msgs as msgs

logger = logging.getLogger("turretd")


@dc.dataclass()
class Turret:
    base_stepper: stepper.BaseStepper
    elev_servo: gpiozero.AngularServo
    trigger_servo: gpiozero.AngularServo
    motor_relay: gpiozero.DigitalOutputDevice
    shots: int = dc.field(default=0, init=False)

    def move(self, base_angle: float, elev_angle: float):
        self.base_stepper.angle = base_angle
        self.elev_servo.angle = elev_angle

    def shoot(self, n: int = 1):
        self.motor_relay.on()
        time.sleep(0.1)

        for _ in range(n):
            self.trigger_servo.angle = -33
            time.sleep(0.1)
            self.trigger_servo.angle = 0
            time.sleep(0.1)

        self.motor_relay.off()
        self.shots += n


def _handle_msg(msg_bytes: bytes, turret: Turret):
    try:
        msg = msgs.decode(msg_bytes, msgs.MoveMsg)
        logger.debug(f"Recieved move message: {msg}")
        turret.move(msg.base_angle, msg.elev_angle)
        return
    except:
        pass

    try:
        msg = msgs.decode(msg_bytes, msgs.ShootMsg)
        logger.debug(f"Recieved shoot message: {msg}")
        turret.shoot(msg.times)
        return
    except:
        pass

    raise ValueError("Unsupported message")


def _handle_connection(conn: socket.socket, turret: Turret):
    while True:
        msg_bytes = conn.recv(4096)

        if not msg_bytes:
            break

        try:
            _handle_msg(msg_bytes, turret)

            resp = msgs.AckMsg()
            resp_bytes = msgs.encode(resp)
            conn.send(resp_bytes)
        except ValueError as e:
            logger.error(e)

    conn.close()


@click.command("turretd")
@click.option("-p", "--port", type=int, default=12345, help="The port to listen on")
@click.option("--debug", is_flag=True, help="show additional debug output")
@click.option(
    "--pin-base-step",
    type=int,
    default=23,
    help="The step pin of the base stepper motor",
)
@click.option(
    "--pin-base-dir",
    type=int,
    default=24,
    help="The direction pin of the base stepper motor",
)
@click.option(
    "--pin-elev-servo", type=int, default=21, help="The elevation servo signal pin"
)
@click.option(
    "--pin-trigger-servo", type=int, default=4, help="The trigger servo signal pin"
)
@click.option(
    "--pin-motor-relay", type=int, default=17, help="The trigger servo signal pin"
)
@click.option("--i2c-bus", type=int, default=1, help="The i2c bus to use")
def main(
    port: int,
    debug: bool,
    pin_base_step: int,
    pin_base_dir: int,
    pin_elev_servo: int,
    pin_trigger_servo: int,
    pin_motor_relay: int,
    i2c_bus: int,
):
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    logging.info("turretd v0.1")
    logging.info(f"{debug=}, {port=}")

    bus = smbus2.SMBus(i2c_bus)
    enc = encoder.Encoder(bus)
    base_stepper = stepper.BaseStepper(
        step_pin=pin_base_step, dir_pin=pin_base_dir, encoder=enc, offset=279.76
    )
    elev_servo = gpiozero.AngularServo(
        pin=pin_elev_servo,
        initial_angle=0,
        min_angle=-90,
        max_angle=90,
        min_pulse_width=0.0005,
        max_pulse_width=0.0025,
    )
    trigger_servo = gpiozero.AngularServo(
        pin=pin_trigger_servo,
        initial_angle=0,
        min_angle=-90,
        max_angle=90,
        min_pulse_width=0.0005,
        max_pulse_width=0.0025,
    )
    motor_relay = gpiozero.DigitalOutputDevice(pin_motor_relay)
    turret = Turret(base_stepper, elev_servo, trigger_servo, motor_relay)
    logger.debug("Configured turret modules")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", port))
    sock.listen(1)

    while True:
        logger.debug("Awaiting connection")
        conn, addr = sock.accept()

        logger.debug(f"Accepted connection from: {addr}")
        _handle_connection(conn, turret)


if __name__ == "__main__":
    main()

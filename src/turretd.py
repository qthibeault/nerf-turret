import dataclasses as dc
import socket
import logging
import pprint as pp

import click
import encoder
import gpiozero
import msgs
import smbus2
import stepper

logger = logging.getLogger("turretd")


@dc.dataclass()
class _Turret:
    base_stepper: stepper.BaseStepper
    elev_servo: gpiozero.AngularServo
    shots: int = dc.field(default=0, init=False)

    @property
    def base_angle(self) -> float:
        return self.base_stepper.angle

    @base_angle.setter
    def base_angle(self, angle: float):
        self.base_stepper.angle = angle

    @property
    def elev_angle(self) -> float:
        return self.elev_servo.angle

    @elev_angle.setter
    def elev_angle(self, angle: float):
        self.elev_servo.angle = angle

    def shoot(self, n: int = 1):
        self.shots += n


def _handle_msg(msg_bytes: bytes, conn: socket.socket, turret: _Turret):
    msg = msgs.decode(msg_bytes)

    if msgs.is_status_req(msg):
        logger.debug("Recieved status request message")
        resp = msgs.status_resp(turret.base_angle, turret.elev_angle, turret.shots)
        resp_bytes = msgs.encode(msg)
        conn.send(resp_bytes)
    elif msgs.is_stepper_msg(msg):
        logger.debug("Recieved angle message")

        for line in pp.pformat(msg).split("\n"):
            logger.debug(line)

        turret.base_angle = msg["base"]
        turret.elev_angle = msg["elevation"]


def _handle_connection(conn: socket.socket, turret: _Turret):
    while True:
        msg_bytes = conn.recv(4096)

        if not msg_bytes:
            break

        _handle_msg(msg_bytes, conn, turret)

    conn.close()


@click.command("turretd")
@click.option("-p", "--port", type=int, default=12345, help="The port to listen on")
@click.option("--debug", is_flag=True)
def main(port: int, debug: bool):
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    logging.info("turretd v0.1")
    logging.info(f"{debug=}, {port=}")

    bus = smbus2.SMBus(1)
    enc = encoder.Encoder(bus)
    base_stepper = stepper.BaseStepper(step_pin=23, dir_pin=24, encoder=enc, offset=279.76)
    elev_servo = gpiozero.AngularServo(
            pin=21,
            initial_angle = 0,
            min_angle=-90,
            max_angle=90,
            min_pulse_width=0.0005,
            max_pulse_width=0.0025
    )
    turret = _Turret(base_stepper, elev_servo)
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

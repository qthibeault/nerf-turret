import socket
from typing import Any

from . import msgs
from .stepper import Stepper, EncoderMultiplexer


def _fire(n: int):
    pass


def main():
    shots = 0
    multiplexer = EncoderMultiplexer(0, 1, 2)
    base_motor = Stepper(3, 4, multiplexer, enc_idx=0)
    elev_motor = Stepper(5, 6, multiplexer, enc_idx=1)

    server_addr = ("0.0.0.0", 80007)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(server_addr)

    should_exit = False

    while not should_exit:
        msg_bytes, addr = s.recvfrom(4096)
        msg: dict[str, Any] = msgs.decode(msg_bytes)

        if msgs.is_stepper_msg(msg):
            if msg["target"] == "base":
                base_motor.to_angle(msg["angle"])
            elif msg["target"] == "elevation":
                elev_motor.to_angle(msg["angle"])
            else:
                raise RuntimeError(f"Unknown stepper command target {msg['target']}")
        elif msgs.is_fire_msg(msg):
            n = msg["count"]
            shots += n
            _fire(n)
        elif msgs.is_status_req(msg):
            with multiplexer.select(base_motor.idx) as base_enc:
                base_angle = base_enc.angle

            with multiplexer.select(elev_motor.idx) as elev_enc:
                elev_angle = elev_enc.angle

            resp = msgs.status_resp(base_angle, elev_angle, shots)
            s.sendto(msgs.encode(resp), addr)


if __name__ == "__main__":
    main()

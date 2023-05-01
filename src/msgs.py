from __future__ import annotations

import json
from typing import Any, TypedDict, Literal

from typing_extensions import TypeGuard


class StepperMsg(TypedDict):
    type: Literal["stepper"]
    base: float
    elevation: float


class FireMsg(TypedDict):
    type: Literal["fire"]
    count: int


class StatusReqMsg(TypedDict):
    type: Literal["status"]


class StatusRespMsg(TypedDict):
    type: Literal["status"]
    base: float
    elevation: float
    shots: int


class StopMsg(TypedDict):
    type: Literal["stop"]


def is_stepper_msg(msg: dict[str, Any]) -> TypeGuard[StepperMsg]:
    return msg["type"] == "stepper"


def is_fire_msg(msg: dict[str, Any]) -> TypeGuard[FireMsg]:
    return msg["type"] == "fire"


def is_status_req(msg: dict[str, Any]) -> TypeGuard[StatusReqMsg]:
    return msg["type"] == "status"


def is_stop_msg(msg: dict[str, Any]) -> TypeGuard[StopMsg]:
    return msg["type"] == "status"


def status_resp(base: float, elevation: float, shots: int) -> StatusRespMsg:
    return {"type": "status", "base": base, "elevation": elevation, "shots": shots}


def encode(msg: StatusRespMsg) -> bytes:
    return json.dumps(msg).encode("utf-8")


def decode(msg: bytes) -> dict[str, Any]:
    return json.loads(msg.decode("utf-8"))

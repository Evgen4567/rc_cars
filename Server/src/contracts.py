import logging
import struct
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Literal, Protocol, Self, TypeVar, runtime_checkable

logger = logging.getLogger(__name__)
BATTERY_MULTIPLIER = 100
SPEED_MULTIPLIER = 100
INT16_OFFSET = 2
INT32_OFFSET = 4
FLOAT32_OFFSET = 4

T = TypeVar("T")
N = TypeVar("N")


def _unpack_data(fmt: Literal["I", "h", "f", "i"], size: int, data: bytes) -> tuple[Any, bytes]:
    value = struct.unpack(fmt, data[:size])[0]
    new_data = data[size:]
    return value, new_data


def _check_type(data: T, expect_type: type[T]) -> None:
    if not isinstance(data, expect_type):
        msg = f"Invalid data type: type={type(data)}, expect={expect_type}, {data=}"
        logger.error(msg)
        raise TypeError(msg)


@runtime_checkable
class AbstractPacket(Protocol):
    @classmethod
    @abstractmethod
    def unpack(cls, data: bytes) -> Self: ...

    @abstractmethod
    def pack(self) -> bytes: ...


# Телеметрия идет Car -> Server -> Client
@dataclass(slots=True)
class CarTelemetry(AbstractPacket):
    frame: bytes
    battery: int
    speed: int
    power: int
    name: str

    @classmethod
    def unpack(cls, data: bytes) -> "CarTelemetry":
        try:
            # Картинка - любое число байтов
            frame_length, data = _unpack_data("I", INT32_OFFSET, data)
            frame = data[:frame_length]
            data = data[frame_length:]

            battery, data = _unpack_data("h", INT16_OFFSET, data)
            speed, data = _unpack_data("h", INT16_OFFSET, data)
            power, data = _unpack_data("h", INT16_OFFSET, data)

            # Имя - любое число байтов
            name_length, data = _unpack_data("h", INT16_OFFSET, data)
            name = data[:name_length].decode("utf-8")
        except struct.error as e:
            msg = "Invalid format of car telemetry packet"
            raise ValueError(msg) from e

        _check_type(frame, bytes)
        _check_type(battery, int)
        _check_type(speed, int)
        _check_type(power, int)
        _check_type(name, str)
        return cls(frame=frame, battery=battery, speed=speed, power=power, name=name)

    def pack(self) -> bytes:
        # Объекты без фиксированной длины
        frame_length = len(self.frame)
        frame_packed = struct.pack("I", frame_length) + self.frame
        name_bytes = self.name.encode("utf-8")
        name_length = len(name_bytes)
        name_packed = struct.pack("h", name_length) + name_bytes

        # int16
        battery_packed = struct.pack("h", self.battery)
        speed_packed = struct.pack("h", self.speed)
        power_packed = struct.pack("h", self.power)
        return frame_packed + battery_packed + speed_packed + power_packed + name_packed


@dataclass(slots=True)
class ClientTelemetry(AbstractPacket):
    frame: bytes
    battery: float
    speed: float
    power: float
    name: str

    @classmethod
    def unpack(cls, data: bytes) -> "ClientTelemetry":
        try:
            # Картинка - любое число байтов
            frame_length, data = _unpack_data("I", INT32_OFFSET, data)
            frame = data[:frame_length]
            data = data[frame_length:]

            # float32
            battery, data = _unpack_data("f", FLOAT32_OFFSET, data)
            speed, data = _unpack_data("f", FLOAT32_OFFSET, data)
            power, data = _unpack_data("f", FLOAT32_OFFSET, data)

            # Имя - любое число байтов
            name_length, data = _unpack_data("h", INT16_OFFSET, data)
            name = data[:name_length].decode("utf-8")

        except struct.error as e:
            msg = "Invalid format of telemetry packet"
            raise ValueError(msg) from e
        _check_type(frame, bytes)
        _check_type(battery, float)
        _check_type(speed, float)
        _check_type(power, float)
        _check_type(name, str)
        return cls(frame=frame, battery=battery, speed=speed, power=power, name=name)

    def pack(self) -> bytes:
        # Объекты без фиксированной длины
        frame_length = len(self.frame)
        frame_packed = struct.pack("I", frame_length) + self.frame

        # float32
        battery_packed = struct.pack("f", self.battery)
        speed_packed = struct.pack("f", self.speed)
        power_packed = struct.pack("f", self.power)

        # Упаковываем name
        name_bytes = self.name.encode("utf-8")
        name_length = len(self.name)
        name_packed = struct.pack("h", name_length) + name_bytes

        # Объединяем все в один байтовый объект
        return frame_packed + battery_packed + speed_packed + power_packed + name_packed


# Сигнал идет Client -> Server -> Car
@dataclass(slots=True)
class CarSignal(AbstractPacket):
    moving: int
    power: int
    direction: int

    @classmethod
    def unpack(cls, data: bytes) -> "CarSignal":
        moving, data = _unpack_data("h", INT16_OFFSET, data)
        power, data = _unpack_data("h", INT16_OFFSET, data)
        direction, data = _unpack_data("h", INT16_OFFSET, data)
        return cls(moving=moving, power=power, direction=direction)

    def pack(self) -> bytes:
        # int16
        moving_bytes = struct.pack("h", self.moving)
        power_bytes = struct.pack("h", self.power)
        direction_bytes = struct.pack("h", self.direction)
        return moving_bytes + power_bytes + direction_bytes


@dataclass(slots=True)
class ClientSignal(AbstractPacket):
    moving: int
    power: int
    direction: int

    @classmethod
    def unpack(cls, data: bytes) -> "ClientSignal":
        moving, data = _unpack_data("h", INT16_OFFSET, data)
        power, data = _unpack_data("h", INT16_OFFSET, data)
        direction, data = _unpack_data("h", INT16_OFFSET, data)
        return cls(moving=moving, power=power, direction=direction)

    def pack(self) -> bytes:
        # int16
        moving_bytes = struct.pack("h", self.moving)
        power_bytes = struct.pack("h", self.power)
        direction_bytes = struct.pack("h", self.direction)
        return moving_bytes + power_bytes + direction_bytes


A = TypeVar("A", bound="AbstractPacket")


def unpack(data: bytes, data_type: type[A]) -> A:
    if not isinstance(data_type, AbstractPacket):
        msg = f"Unsupported data type: {type(data).__name__}"
        raise TypeError(msg)
    return data_type.unpack(data)


def pack(data: A) -> bytes:
    if not isinstance(data, AbstractPacket):
        msg = f"Unsupported data type: {type(data).__name__}"
        raise TypeError(msg)
    return data.pack()


def repack(data: T, new_type: type[N]) -> N:
    if isinstance(data, CarTelemetry) and new_type is ClientTelemetry:
        return ClientTelemetry(  # type: ignore[return-value]
            frame=data.frame,
            battery=data.battery / BATTERY_MULTIPLIER,
            speed=data.speed / SPEED_MULTIPLIER,
            power=data.power / SPEED_MULTIPLIER,
            name=data.name,
        )
    if isinstance(data, ClientSignal) and new_type is CarSignal:
        return CarSignal(moving=data.moving, power=data.power, direction=data.direction)  # type: ignore[return-value]
    msg = (
        f"Forbidden repack: {type(data)} to {new_type}"
        "\nIt can only be:"
        "\nCarTelemetry -> ClientTelemetry"
        "\nClientSignal -> CarSignal"
    )
    raise ValueError(msg)

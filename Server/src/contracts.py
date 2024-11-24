from collections import namedtuple
import logging
import struct
from typing import Any, Literal, TypeVar

logger = logging.getLogger(__name__)
BATTERY_MULTIPLIER = 100
SPEED_MULTIPLIER = 100
INT16_OFFSET = 2
INT32_OFFSET = 4
FLOAT32_OFFSET = 4

# Телеметрия идет Car -> Server -> Client
CarTelemetry = namedtuple('CarTelemetry', ["frame", "battery", "speed", "power", "name"])
ClientTelemetry = namedtuple('ClientTelemetry', ["frame", "battery", "speed", "power", "name"])

# Сигнал идет Client -> Server -> Car
CarSignal = namedtuple('ControlSignal', ["moving", "power", "direction"])
ClientSignal = namedtuple('ClientSignal', ["moving", "power", "direction"])

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

def _unpack_car_telemetry(data: bytes) -> CarTelemetry:
    try:
        # Картинка - любое число байтов
        frame_length, data = _unpack_data("I", INT32_OFFSET, data)
        frame = data[:frame_length]
        data = data[frame_length:]

        battery, data = _unpack_data("h", INT16_OFFSET, data)
        speed, data = _unpack_data("h", INT16_OFFSET, data)
        power, data = _unpack_data("h", INT16_OFFSET, data)

        # Имя - любое число байтов
        name_length, data = _unpack_data("I", INT16_OFFSET, data)
        name = data[:name_length].decode("utf-8")
    except struct.error as e:
        msg = "Invalid format of car telemetry packet"
        raise ValueError(msg) from e
    
    _check_type(frame, bytes)
    _check_type(battery, int)
    _check_type(speed, int)
    _check_type(power, int)
    _check_type(name, str)
    return CarTelemetry(frame=frame, battery=battery, speed=speed, power=power, name=name)

def _pack_car_telemetry(car_telemetry: CarTelemetry) -> bytes:
    # Объекты без фиксированной длины
    frame_length = len(car_telemetry.frame)
    frame_packed = struct.pack("I", frame_length) + car_telemetry.frame
    name_bytes = car_telemetry.name.encode("utf-8")
    name_length = len(name_bytes)
    name_packed = struct.pack("h", name_length) + name_bytes

    # int16
    battery_packed = struct.pack("h", car_telemetry.battery)
    speed_packed = struct.pack("h", car_telemetry.speed)
    power_packed = struct.pack("h", car_telemetry.power)
    return frame_packed + battery_packed + speed_packed + power_packed + name_packed

def _unpack_client_telemetry(data: bytes) -> ClientTelemetry:
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
    return ClientTelemetry(frame=frame, battery=battery, speed=speed, power=power, name=name)

def _pack_client_telemetry(client_telemetry: ClientTelemetry) -> bytes:
    # Объекты без фиксированной длины
    frame_length = len(client_telemetry.frame)
    frame_packed = struct.pack("I", frame_length) + client_telemetry.frame

    # float32
    battery_packed = struct.pack("f", client_telemetry.battery)
    speed_packed = struct.pack("f", client_telemetry.speed)
    power_packed = struct.pack("f", client_telemetry.power)

    # Упаковываем name
    name_bytes = client_telemetry.name.encode("utf-8")
    name_length = len(client_telemetry.name)
    name_packed = struct.pack("h", name_length) + name_bytes

    # Объединяем все в один байтовый объект
    return frame_packed + battery_packed + speed_packed + power_packed + name_packed

def _unpack_car_signal(data: bytes) -> CarSignal:
    moving, data = _unpack_data("h", INT16_OFFSET, data)
    power, data = _unpack_data("h", INT16_OFFSET, data)
    direction, data = _unpack_data("h", INT16_OFFSET, data)    
    return CarSignal(moving=moving, power=power, direction=direction)

def _pack_car_signal(car_signal: CarSignal) -> bytes:
    # int16
    moving_bytes = struct.pack("h", car_signal.moving)
    power_bytes = struct.pack("h", car_signal.power)
    direction_bytes = struct.pack("h", car_signal.direction)
    return moving_bytes + power_bytes + direction_bytes

def _unpack_client_signal(data: bytes) -> ClientSignal:
    moving, data = _unpack_data("h", INT16_OFFSET, data)
    power, data = _unpack_data("h", INT16_OFFSET, data)
    direction, data = _unpack_data("h", INT16_OFFSET, data)
    return ClientSignal(moving=moving, power=power, direction=direction)

def _pack_client_signal(client_signal: ClientSignal) -> bytes:
    # int16
    moving_bytes = struct.pack("h", client_signal.moving)
    power_bytes = struct.pack("h", client_signal.power)
    direction_bytes = struct.pack("h", client_signal.direction)
    return moving_bytes + power_bytes + direction_bytes

def unpack(data: bytes, data_type: type[T]) -> T:
    match data_type:
        case _ if data_type is CarTelemetry:
            return _unpack_car_telemetry(data)
        case _ if data_type is CarSignal:
            return _unpack_car_signal(data)
        case _ if data_type is ClientTelemetry:
            return _unpack_client_telemetry(data)
        case _ if data_type is ClientSignal:
            return _unpack_client_signal(data)
        case _:
            raise ValueError(f"Unsupported data type: {data_type}")
        
def pack(data: T) -> bytes:
    match data:
        case _ if isinstance(data, CarTelemetry):
            return _pack_car_telemetry(data)
        case _ if isinstance(data, CarSignal):
            return _pack_car_signal(data)
        case _ if isinstance(data, ClientTelemetry):
            return _pack_client_telemetry(data)
        case _ if isinstance(data, ClientSignal):
            return _pack_client_signal(data)
        case _:
            raise ValueError(f"Unsupported data type: {data}")
        
def repack(data: T, new_type: type[N]) -> N:
    if isinstance(data, CarTelemetry) and new_type is ClientTelemetry:
        return ClientTelemetry(
            frame=data.frame, 
            battery=data.battery / BATTERY_MULTIPLIER, 
            speed=data.speed / SPEED_MULTIPLIER,
            power=data.power / SPEED_MULTIPLIER,
            name=data.name
        )
    elif isinstance(data, ClientSignal) and new_type is CarSignal:
        return CarSignal(
            moving=data.moving, 
            power=data.power, 
            direction=data.direction
        )
    else:
        raise ValueError(
            f"Forbidden repack: {type(data)} to {new_type}"
            "\nIt can only be:"
            "\nCarTelemetry -> ClientTelemetry"
            "\nClientSignal -> CarSignal"
        )

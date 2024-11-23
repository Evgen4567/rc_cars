from collections import namedtuple
import logging
import struct
from typing import TypeVar

logger = logging.getLogger(__name__)
BATTERY_MULTIPLIER = 100
SPEED_MULTIPLIER = 100

# Телеметрия идет Car -> Server -> Client
CarTelemetry = namedtuple('CarTelemetry', ["frame", "battery", "speed", "power", "name"])
ClientTelemetry = namedtuple('ClientTelemetry', ["frame", "battery", "speed", "power", "name"])

# Сигнал идет Client -> Server -> Car
CarSignal = namedtuple('ControlSignal', ["moving", "power", "direction"])
ClientSignal = namedtuple('ClientSignal', ["moving", "power", "direction"])

T = TypeVar("T")
N = TypeVar("N")

def _check_type(data: T, expect_type: type[T]) -> None:
    if not isinstance(data, expect_type):
        msg = f"Invalid data type: type={type(data)}, expect={expect_type}, {data=}"
        logger.error(msg)
        raise TypeError(msg)

def _unpack_car_telemetry(data: bytes) -> CarTelemetry:
    offset = 0
    try:
        # Распаковываем frame
        frame_length = struct.unpack("I", data[offset:offset + 4])[0]
        offset += 4
        frame = data[offset:offset + frame_length]
        offset += frame_length
        # Распаковываем battery
        battery = struct.unpack("i", data[offset:offset + 4])[0]
        offset += 4
        # Распаковываем speed
        speed = struct.unpack("i", data[offset:offset + 4])[0]
        offset += 4
        # Распаковываем power
        power = struct.unpack("i", data[offset:offset + 4])[0]
        offset += 4
        # Распаковываем id
        name_length = struct.unpack("I", data[offset:offset + 4])[0]
        offset += 4
        name = data[offset:offset + name_length].decode("utf-8")
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
    # Упаковываем frame: длина кадра + сам кадр (байты)
    frame_length = len(car_telemetry.frame)
    frame_packed = struct.pack("I", frame_length) + car_telemetry.frame

    # Упаковываем battery как 4-байтовое целое число (int)
    battery_packed = struct.pack("i", car_telemetry.battery)

    # Упаковываем speed как 4-байтовое целое число (int)
    speed_packed = struct.pack("i", car_telemetry.speed)

    # Упаковываем power как 4-байтовое целое число (int)
    power_packed = struct.pack("i", car_telemetry.power)

    # Упаковываем id: длина строки + сама строка (байты)
    name_bytes = car_telemetry.id.encode("utf-8")
    name_length = len(name_bytes)
    name_packed = struct.pack("I", name_length) + name_bytes

    # Объединяем все в один байтовый объект
    return frame_packed + battery_packed + speed_packed + power_packed + name_packed

def _unpack_client_telemetry(data: bytes) -> ClientTelemetry:
    offset = 0
    try:
        # Распаковываем длину кадра и сам кадр
        frame_length = struct.unpack("I", data[offset:offset + 4])[0]
        offset += 4
        frame = data[offset:offset + frame_length]
        offset += frame_length
        
        # Распаковываем другие данные
        battery = struct.unpack("f", data[offset:offset + 4])[0]
        offset += 4
        speed = struct.unpack("f", data[offset:offset + 4])[0]
        offset += 4
        power = struct.unpack("f", data[offset:offset + 4])[0]
        offset += 4
        
        # Распаковываем длину имени и само имя
        name_length = struct.unpack("I", data[offset:offset + 4])[0]
        offset += 4
        name = data[offset:offset + name_length].decode("utf-8")

    except struct.error as e:
        msg = "Invalid format of telemetry packet"
        raise ValueError(msg) from e
    _check_type(frame, bytes)
    _check_type(battery, float)
    _check_type(speed, float)
    _check_type(power, float)
    _check_type(name, float)
    return ClientTelemetry(frame=frame, battery=battery, speed=speed, power=power, name=name)

def _pack_client_telemetry(client_telemetry: ClientTelemetry) -> bytes:
    # Упаковываем frame: длина кадра + сам кадр (байты)
    frame_length = len(client_telemetry.frame)
    frame_packed = struct.pack("I", frame_length) + client_telemetry.frame

    # Упаковываем battery как 4-байтовое целое число (int)
    battery_packed = struct.pack("f", client_telemetry.battery)

    # Упаковываем speed как 4-байтовое целое число (int)
    speed_packed = struct.pack("f", client_telemetry.speed)

    # Упаковываем power как 4-байтовое целое число (int)
    power_packed = struct.pack("f", client_telemetry.power)

    # Упаковываем id: длина строки + сама строка (байты)
    name_bytes = client_telemetry.name.encode("utf-8")
    name_length = len(client_telemetry.name)
    name_packed = struct.pack("I", name_length) + name_bytes

    # Объединяем все в один байтовый объект
    return frame_packed + battery_packed + speed_packed + power_packed + name_packed

def _unpack_car_signal(data: bytes) -> CarSignal:
    # Распаковываем moving, power и direction как 4-байтовые целые числа
    moving = struct.unpack("i", data[:4])[0]
    power = struct.unpack("i", data[4:8])[0]
    direction = struct.unpack("i", data[8:12])[0]
    
    return CarSignal(moving=moving, power=power, direction=direction)

def _pack_car_signal(car_signal: CarSignal) -> bytes:
    # Упаковываем moving как 4-байтовое целое число (int)
    moving_bytes = struct.pack("i", car_signal.moving)

    # Упаковываем power как 4-байтовое целое число (int)
    power_bytes = struct.pack("i", car_signal.power)

    # Упаковываем direction как 4-байтовое целое число (int)
    direction_bytes = struct.pack("i", car_signal.direction)

    # Объединяем все в один байтовый объект
    return moving_bytes + power_bytes + direction_bytes

def _unpack_client_signal(data: bytes) -> ClientSignal:
    # Распаковываем moving, power и direction как 4-байтовые целые числа
    moving = struct.unpack("i", data[:4])[0]
    power = struct.unpack("i", data[4:8])[0]
    direction = struct.unpack("i", data[8:12])[0]
    
    return ClientSignal(moving=moving, power=power, direction=direction)

def _pack_client_signal(client_signal: ClientSignal) -> bytes:
    # Упаковываем moving как 4-байтовое целое число (int)
    moving_bytes = struct.pack("i", client_signal.moving)

    # Упаковываем power как 4-байтовое целое число (int)
    power_bytes = struct.pack("i", client_signal.power)

    # Упаковываем direction как 4-байтовое целое число (int)
    direction_bytes = struct.pack("i", client_signal.direction)

    # Объединяем все в один байтовый объект
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
            battery=data.frame * BATTERY_MULTIPLIER, 
            speed=data.speed * SPEED_MULTIPLIER,
            power=data.speed * SPEED_MULTIPLIER,
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
            "\CarTelemetry -> ClientTelemetry"
            "\ClientSignal -> CarSignal"
        )

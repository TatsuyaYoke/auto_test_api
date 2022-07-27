from __future__ import annotations

import struct
from typing import Optional, cast

import serial
from serial.serialutil import SerialTimeoutException

import common.settings
from common.logger import set_logger

LOGGER_IS_ACTIVE_STREAM = common.settings.logger_is_active_stream
logger = set_logger(__name__, is_active_stream=LOGGER_IS_ACTIVE_STREAM)


class SerialDriver:
    def __init__(self) -> None:
        self.__ser = None
        self.__is_connection_error = False

    def set_port(
        self,
        port: str,
        baudrate: int,
        parity: str = "N",
        datasize: int = 8,
        stopbits: int = 1,
        timeout: float = 1,
        write_timeout: float = 1,
        txrx_size: int = 4096,
    ) -> None:
        if self.__ser is None or not self.__ser.is_open:
            self.__ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                parity=parity,
                bytesize=datasize,
                stopbits=stopbits,
                timeout=timeout,
                writeTimeout=write_timeout,
            )
            if self.__ser is not None:
                self.__ser.set_buffer_size(rx_size=txrx_size, tx_size=txrx_size)

    def close_port(self) -> None:
        if self.__ser is not None:
            self.__ser.close()

    def send_binary_array(self, data: list[int]) -> None:

        if self.__ser is None:
            self.__is_connection_error = False
            logger.error("Serial is None!")
        else:
            while True:
                if self.__ser.out_waiting == 0:
                    break
            try:
                for c in data:
                    self.__ser.write(struct.pack("B", c))
                self.__is_connection_error = False
                self.__ser.flush()
            except SerialTimeoutException:
                self.__is_connection_error = True
                logger.error("Serial write timeout!")

    def send_ascii(self, data: str, termination: str = "\r\n") -> None:
        if self.__ser is None:
            self.__is_connection_error = False
            logger.error("Serial is None!")
        else:
            while True:
                if self.__ser.out_waiting == 0:
                    break
            try:
                self.__ser.write((data + termination).encode())
                self.__is_connection_error = False
                self.__ser.flush()
            except SerialTimeoutException:
                self.__is_connection_error = True
                logger.error("Serial write timeout!")

    def receive_binary(self) -> Optional[str]:

        if self.__ser is None:
            self.__is_connection_error = False
            logger.error("Serial is None!")
            return None
        else:
            try:
                while True:
                    if self.__ser.in_waiting > 0:
                        break

                data_bytes: bytes = self.__ser.read(self.__ser.in_waiting)
                self.__is_connection_error = False
                return data_bytes.hex()
            except struct.error:
                return None
            except SerialTimeoutException:
                self.__is_connection_error = True
                logger.error("Serial timeout!")
                return None

    def receive_ascii(self) -> Optional[str]:
        if self.__ser is None:
            self.__is_connection_error = False
            logger.error("Serial is None!")
            return None
        else:
            try:
                while True:
                    if self.__ser.in_waiting > 0:
                        break

                self.__is_connection_error = False
                return cast(bytes, self.__ser.read(self.__ser.in_waiting)).decode()

            except SerialTimeoutException:
                self.__is_connection_error = True
                logger.error("Serial timeout!")
                return None

    def get_port_status(self) -> bool:
        if self.__ser is None:
            return False
        else:
            return self.__ser.is_open

    def get_connection_status(self) -> bool:
        return self.__is_connection_error

#!/usr/bin/env python3
"""Tritech Micron commands."""

import bitstring

__author__ = "Anass Al-Wohoush, Erin Havens"


class Command(object):

    """Sonar command."""

    def __init__(self, id, payload=None):
        """Constructs Command object.

        Args:
            id: Message ID.
            payload: Message payload (optional).
        """
        self.id = id
        self.payload = payload if payload else bitstring.BitStream()
        self.size = int((self.payload.length / 8) + 8)

    def serialize(self):
        """Constructs corresponding string of bytes to send to sonar.

        Returns:
            String representation of data.
        """
        payload_length = self.payload.length//8
        if self.id == 25:
            print("in id=25")
            # self.size = 67
            header = bitstring.BitStream(hex='4030303043')
            # Add the fixed part of the message
            fixed_part = bitstring.BitStream(hex='0C00FF0207198002')
            values = {
                "payload_length": self.payload.length,
                "payload": self.payload
            }
            serial_format = ("bits:payload_length=payload, 0x0A")
            payload_msg = bitstring.pack(serial_format, **values)
            message = header + fixed_part + payload_msg
            return message.tobytes()



        
        hex_size = bytearray("{:04x}".format(self.size), 'utf-8')
        values = {
            "id": self.id,
            "hex": hex_size,
            "bin": self.size,
            "bytes_left": self.size - 5,
            "payload_length": self.payload.length,
            "payload": self.payload
        }
        serial_format = (
            "0x40, bits:32=hex, uintle:16=bin, 0xFF, 0x02, uint:8=bytes_left,"
            "uint:8=id, 0x80, 0x02, bits:payload_length=payload, 0x0A")
        
        message = bitstring.pack(serial_format, **values)
        print(f"payload_size:{self.size}")

        # print("Field lengths (in bytes):")
        # print(f"Header '@': {1}")
        # print(f"Hex length: {len(values['hex'])}")
        # print(f"Binary length: {2}")
        # print(f"Tx Node: {1}")
        # print(f"Rx Node: {1}")
        # print(f"No. of bytes: {1}")
        # print(f"Message ID: {1}")
        # print(f"Sequence: {1}")
        # print(f"Node ID: {1}")
        # print(f"Payload: {len(self.payload.tobytes())}")
        # print(f"Line Feed: {1}")
        return message.tobytes()
"""USB HID report descriptors presented to the target computer.

The keyboard descriptor is the canonical boot-protocol keyboard descriptor
from the USB HID 1.11 specification (Appendix E.6), byte for byte.  The
relative mouse descriptor is the boot-protocol mouse (Appendix E.10) with the
ubiquitous wheel byte appended; the first three report bytes are exactly the
boot mouse format, so the device stays usable when a BIOS/UEFI switches it to
boot protocol with SET_PROTOCOL.
"""
from __future__ import annotations

KEYBOARD_REPORT_LENGTH = 8
KEYBOARD_OUTPUT_LENGTH = 1  # LED report


def keyboard_report_descriptor(extended: bool = False) -> bytes:
    """Return the keyboard report descriptor.

    ``extended=False`` is the exact 63-byte HID spec boot keyboard descriptor
    (array usages 0x00-0x65).  ``extended=True`` widens the key array to
    0x00-0xFF so that F13-F24, international and keypad-extra keys can be
    delivered; the report format is unchanged and still boot compatible.
    """
    if extended:
        key_array = bytes([
            0x95, 0x06,        # Report Count (6)
            0x75, 0x08,        # Report Size (8)
            0x15, 0x00,        # Logical Minimum (0)
            0x26, 0xFF, 0x00,  # Logical Maximum (255)
            0x05, 0x07,        # Usage Page (Key Codes)
            0x19, 0x00,        # Usage Minimum (0)
            0x2A, 0xFF, 0x00,  # Usage Maximum (255)
            0x81, 0x00,        # Input (Data, Array)
        ])
    else:
        key_array = bytes([
            0x95, 0x06,  # Report Count (6)
            0x75, 0x08,  # Report Size (8)
            0x15, 0x00,  # Logical Minimum (0)
            0x25, 0x65,  # Logical Maximum (101)
            0x05, 0x07,  # Usage Page (Key Codes)
            0x19, 0x00,  # Usage Minimum (0)
            0x29, 0x65,  # Usage Maximum (101)
            0x81, 0x00,  # Input (Data, Array)
        ])
    return bytes([
        0x05, 0x01,  # Usage Page (Generic Desktop)
        0x09, 0x06,  # Usage (Keyboard)
        0xA1, 0x01,  # Collection (Application)
        0x05, 0x07,  #   Usage Page (Key Codes)
        0x19, 0xE0,  #   Usage Minimum (224)
        0x29, 0xE7,  #   Usage Maximum (231)
        0x15, 0x00,  #   Logical Minimum (0)
        0x25, 0x01,  #   Logical Maximum (1)
        0x75, 0x01,  #   Report Size (1)
        0x95, 0x08,  #   Report Count (8)
        0x81, 0x02,  #   Input (Data, Variable, Absolute)  ; modifier byte
        0x95, 0x01,  #   Report Count (1)
        0x75, 0x08,  #   Report Size (8)
        0x81, 0x01,  #   Input (Constant)                   ; reserved byte
        0x95, 0x05,  #   Report Count (5)
        0x75, 0x01,  #   Report Size (1)
        0x05, 0x08,  #   Usage Page (LEDs)
        0x19, 0x01,  #   Usage Minimum (1)
        0x29, 0x05,  #   Usage Maximum (5)
        0x91, 0x02,  #   Output (Data, Variable, Absolute) ; LED report
        0x95, 0x01,  #   Report Count (1)
        0x75, 0x03,  #   Report Size (3)
        0x91, 0x01,  #   Output (Constant)                  ; LED padding
    ]) + key_array + bytes([
        0xC0,        # End Collection
    ])


def mouse_report_descriptor(mode: str = "relative", buttons: int = 3) -> bytes:
    """Return the mouse report descriptor for ``mode`` ("relative"/"absolute")."""
    if buttons not in (3, 5):
        raise ValueError("mouse buttons must be 3 or 5")
    padding_bits = 8 - buttons
    header = bytes([
        0x05, 0x01,           # Usage Page (Generic Desktop)
        0x09, 0x02,           # Usage (Mouse)
        0xA1, 0x01,           # Collection (Application)
        0x09, 0x01,           #   Usage (Pointer)
        0xA1, 0x00,           #   Collection (Physical)
        0x05, 0x09,           #     Usage Page (Buttons)
        0x19, 0x01,           #     Usage Minimum (1)
        0x29, buttons,        #     Usage Maximum (n)
        0x15, 0x00,           #     Logical Minimum (0)
        0x25, 0x01,           #     Logical Maximum (1)
        0x95, buttons,        #     Report Count (n)
        0x75, 0x01,           #     Report Size (1)
        0x81, 0x02,           #     Input (Data, Variable, Absolute) ; buttons
        0x95, 0x01,           #     Report Count (1)
        0x75, padding_bits,   #     Report Size (8-n)
        0x81, 0x01,           #     Input (Constant)                 ; padding
        0x05, 0x01,           #     Usage Page (Generic Desktop)
    ])
    if mode == "relative":
        axes = bytes([
            0x09, 0x30,  #     Usage (X)
            0x09, 0x31,  #     Usage (Y)
            0x09, 0x38,  #     Usage (Wheel)
            0x15, 0x81,  #     Logical Minimum (-127)
            0x25, 0x7F,  #     Logical Maximum (127)
            0x75, 0x08,  #     Report Size (8)
            0x95, 0x03,  #     Report Count (3)
            0x81, 0x06,  #     Input (Data, Variable, Relative)
        ])
    elif mode == "absolute":
        axes = bytes([
            0x09, 0x30,        #     Usage (X)
            0x09, 0x31,        #     Usage (Y)
            0x15, 0x00,        #     Logical Minimum (0)
            0x26, 0xFF, 0x7F,  #     Logical Maximum (32767)
            0x75, 0x10,        #     Report Size (16)
            0x95, 0x02,        #     Report Count (2)
            0x81, 0x02,        #     Input (Data, Variable, Absolute)
            0x09, 0x38,        #     Usage (Wheel)
            0x15, 0x81,        #     Logical Minimum (-127)
            0x25, 0x7F,        #     Logical Maximum (127)
            0x75, 0x08,        #     Report Size (8)
            0x95, 0x01,        #     Report Count (1)
            0x81, 0x06,        #     Input (Data, Variable, Relative)
        ])
    else:
        raise ValueError(f"unknown mouse mode {mode!r}")
    return header + axes + bytes([
        0xC0,  #   End Collection
        0xC0,  # End Collection
    ])


def mouse_report_length(mode: str) -> int:
    if mode == "relative":
        return 4  # buttons, x, y, wheel
    if mode == "absolute":
        return 6  # buttons, x(16), y(16), wheel
    raise ValueError(f"unknown mouse mode {mode!r}")


ABS_MAX_VALUE = 0x7FFF

# HID interface subclass/protocol constants
HID_SUBCLASS_NONE = 0
HID_SUBCLASS_BOOT = 1
HID_PROTOCOL_NONE = 0
HID_PROTOCOL_KEYBOARD = 1
HID_PROTOCOL_MOUSE = 2


def report_bit_sizes(descriptor: bytes) -> tuple[int, int]:
    """Parse a report descriptor and return (input_bits, output_bits).

    A tiny short-item parser used by the tests and by ``hid-bridge check`` to
    prove that the declared report lengths match what the descriptor encodes.
    Report IDs are deliberately unsupported: a generic keyboard uses none.
    """
    input_bits = 0
    output_bits = 0
    report_size = 0
    report_count = 0
    i = 0
    depth = 0
    while i < len(descriptor):
        prefix = descriptor[i]
        i += 1
        if prefix == 0xFE:
            raise ValueError("long items are not supported")
        size = prefix & 0x03
        if size == 3:
            size = 4
        item_type = (prefix >> 2) & 0x03
        tag = prefix >> 4
        data = int.from_bytes(descriptor[i:i + size], "little") if size else 0
        i += size
        if item_type == 0:  # main
            if tag == 0x8:
                input_bits += report_size * report_count
            elif tag == 0x9:
                output_bits += report_size * report_count
            elif tag == 0xA:
                depth += 1
            elif tag == 0xC:
                depth -= 1
        elif item_type == 1:  # global
            if tag == 0x7:
                report_size = data
            elif tag == 0x9:
                report_count = data
            elif tag == 0x8:
                raise ValueError("report IDs are not used by this project")
    if depth != 0:
        raise ValueError("unbalanced collections")
    return input_bits, output_bits

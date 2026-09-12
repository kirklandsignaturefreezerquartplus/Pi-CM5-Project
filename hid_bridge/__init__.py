"""hid-bridge: a Raspberry Pi CM5 USB-gadget HID bridge.

The CM5 enumerates on its USB device port as a plain full-speed USB HID
keyboard + mouse (boot-protocol, no vendor extensions, no composite
class markers) and re-transmits input received from a PiKVM and from
local macro devices attached to its USB host ports.
"""

__version__ = "0.1.0"

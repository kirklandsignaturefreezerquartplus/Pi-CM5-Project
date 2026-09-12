"""Key code tables.

* ``KEY_CODES``      evdev key names -> evdev codes (<linux/input-event-codes.h>)
* ``EVDEV_TO_HID``   evdev key codes -> USB HID Keyboard/Keypad page usage IDs
* ``KEY_ALIASES``    friendly names used in macro definitions -> HID usage IDs
* ``US_LAYOUT``      printable characters -> (usage, needs_shift) for ``type``

``EVDEV_TO_HID`` is the inverse of the ``hid_keyboard[]`` table in the Linux
kernel's ``drivers/hid/hid-input.c`` restricted to usages a plain boot
protocol keyboard emits (0x04-0xA4 plus the 0xE0-0xE7 modifiers).
"""
from __future__ import annotations

KEY_CODES: dict[str, int] = {
    "KEY_ESC": 1, "KEY_1": 2, "KEY_2": 3, "KEY_3": 4, "KEY_4": 5, "KEY_5": 6,
    "KEY_6": 7, "KEY_7": 8, "KEY_8": 9, "KEY_9": 10, "KEY_0": 11,
    "KEY_MINUS": 12, "KEY_EQUAL": 13, "KEY_BACKSPACE": 14, "KEY_TAB": 15,
    "KEY_Q": 16, "KEY_W": 17, "KEY_E": 18, "KEY_R": 19, "KEY_T": 20, "KEY_Y": 21,
    "KEY_U": 22, "KEY_I": 23, "KEY_O": 24, "KEY_P": 25,
    "KEY_LEFTBRACE": 26, "KEY_RIGHTBRACE": 27, "KEY_ENTER": 28, "KEY_LEFTCTRL": 29,
    "KEY_A": 30, "KEY_S": 31, "KEY_D": 32, "KEY_F": 33, "KEY_G": 34, "KEY_H": 35,
    "KEY_J": 36, "KEY_K": 37, "KEY_L": 38,
    "KEY_SEMICOLON": 39, "KEY_APOSTROPHE": 40, "KEY_GRAVE": 41, "KEY_LEFTSHIFT": 42,
    "KEY_BACKSLASH": 43,
    "KEY_Z": 44, "KEY_X": 45, "KEY_C": 46, "KEY_V": 47, "KEY_B": 48, "KEY_N": 49, "KEY_M": 50,
    "KEY_COMMA": 51, "KEY_DOT": 52, "KEY_SLASH": 53, "KEY_RIGHTSHIFT": 54,
    "KEY_KPASTERISK": 55, "KEY_LEFTALT": 56, "KEY_SPACE": 57, "KEY_CAPSLOCK": 58,
    "KEY_F1": 59, "KEY_F2": 60, "KEY_F3": 61, "KEY_F4": 62, "KEY_F5": 63, "KEY_F6": 64,
    "KEY_F7": 65, "KEY_F8": 66, "KEY_F9": 67, "KEY_F10": 68,
    "KEY_NUMLOCK": 69, "KEY_SCROLLLOCK": 70,
    "KEY_KP7": 71, "KEY_KP8": 72, "KEY_KP9": 73, "KEY_KPMINUS": 74,
    "KEY_KP4": 75, "KEY_KP5": 76, "KEY_KP6": 77, "KEY_KPPLUS": 78,
    "KEY_KP1": 79, "KEY_KP2": 80, "KEY_KP3": 81, "KEY_KP0": 82, "KEY_KPDOT": 83,
    "KEY_ZENKAKUHANKAKU": 85, "KEY_102ND": 86, "KEY_F11": 87, "KEY_F12": 88,
    "KEY_RO": 89, "KEY_KATAKANA": 90, "KEY_HIRAGANA": 91, "KEY_HENKAN": 92,
    "KEY_KATAKANAHIRAGANA": 93, "KEY_MUHENKAN": 94, "KEY_KPJPCOMMA": 95,
    "KEY_KPENTER": 96, "KEY_RIGHTCTRL": 97, "KEY_KPSLASH": 98, "KEY_SYSRQ": 99,
    "KEY_RIGHTALT": 100, "KEY_LINEFEED": 101,
    "KEY_HOME": 102, "KEY_UP": 103, "KEY_PAGEUP": 104, "KEY_LEFT": 105, "KEY_RIGHT": 106,
    "KEY_END": 107, "KEY_DOWN": 108, "KEY_PAGEDOWN": 109, "KEY_INSERT": 110, "KEY_DELETE": 111,
    "KEY_MACRO": 112, "KEY_MUTE": 113, "KEY_VOLUMEDOWN": 114, "KEY_VOLUMEUP": 115,
    "KEY_POWER": 116, "KEY_KPEQUAL": 117, "KEY_KPPLUSMINUS": 118, "KEY_PAUSE": 119,
    "KEY_SCALE": 120, "KEY_KPCOMMA": 121, "KEY_HANGEUL": 122, "KEY_HANJA": 123,
    "KEY_YEN": 124, "KEY_LEFTMETA": 125, "KEY_RIGHTMETA": 126, "KEY_COMPOSE": 127,
    "KEY_STOP": 128, "KEY_AGAIN": 129, "KEY_PROPS": 130, "KEY_UNDO": 131, "KEY_FRONT": 132,
    "KEY_COPY": 133, "KEY_OPEN": 134, "KEY_PASTE": 135, "KEY_FIND": 136, "KEY_CUT": 137,
    "KEY_HELP": 138, "KEY_MENU": 139, "KEY_CALC": 140, "KEY_SETUP": 141, "KEY_SLEEP": 142,
    "KEY_WAKEUP": 143, "KEY_FILE": 144, "KEY_SENDFILE": 145, "KEY_DELETEFILE": 146,
    "KEY_XFER": 147, "KEY_PROG1": 148, "KEY_PROG2": 149, "KEY_WWW": 150, "KEY_MSDOS": 151,
    "KEY_COFFEE": 152, "KEY_ROTATE_DISPLAY": 153, "KEY_CYCLEWINDOWS": 154, "KEY_MAIL": 155,
    "KEY_BOOKMARKS": 156, "KEY_COMPUTER": 157, "KEY_BACK": 158, "KEY_FORWARD": 159,
    "KEY_CLOSECD": 160, "KEY_EJECTCD": 161, "KEY_EJECTCLOSECD": 162, "KEY_NEXTSONG": 163,
    "KEY_PLAYPAUSE": 164, "KEY_PREVIOUSSONG": 165, "KEY_STOPCD": 166, "KEY_RECORD": 167,
    "KEY_REWIND": 168, "KEY_PHONE": 169, "KEY_ISO": 170, "KEY_CONFIG": 171,
    "KEY_HOMEPAGE": 172, "KEY_REFRESH": 173, "KEY_EXIT": 174, "KEY_MOVE": 175, "KEY_EDIT": 176,
    "KEY_SCROLLUP": 177, "KEY_SCROLLDOWN": 178, "KEY_KPLEFTPAREN": 179, "KEY_KPRIGHTPAREN": 180,
    "KEY_NEW": 181, "KEY_REDO": 182,
    "KEY_F13": 183, "KEY_F14": 184, "KEY_F15": 185, "KEY_F16": 186, "KEY_F17": 187,
    "KEY_F18": 188, "KEY_F19": 189, "KEY_F20": 190, "KEY_F21": 191, "KEY_F22": 192,
    "KEY_F23": 193, "KEY_F24": 194,
    "KEY_PLAYCD": 200, "KEY_PAUSECD": 201, "KEY_PROG3": 202, "KEY_PROG4": 203,
    "KEY_ALL_APPLICATIONS": 204, "KEY_SUSPEND": 205, "KEY_CLOSE": 206, "KEY_PLAY": 207,
    "KEY_FASTFORWARD": 208, "KEY_BASSBOOST": 209, "KEY_PRINT": 210, "KEY_HP": 211,
    "KEY_CAMERA": 212, "KEY_SOUND": 213, "KEY_QUESTION": 214, "KEY_EMAIL": 215,
    "KEY_CHAT": 216, "KEY_SEARCH": 217, "KEY_CONNECT": 218, "KEY_FINANCE": 219,
    "KEY_SPORT": 220, "KEY_SHOP": 221, "KEY_ALTERASE": 222, "KEY_CANCEL": 223,
    "KEY_BRIGHTNESSDOWN": 224, "KEY_BRIGHTNESSUP": 225, "KEY_MEDIA": 226,
    "KEY_SWITCHVIDEOMODE": 227, "KEY_KBDILLUMTOGGLE": 228, "KEY_KBDILLUMDOWN": 229,
    "KEY_KBDILLUMUP": 230, "KEY_SEND": 231, "KEY_REPLY": 232, "KEY_FORWARDMAIL": 233,
    "KEY_SAVE": 234, "KEY_DOCUMENTS": 235, "KEY_BATTERY": 236, "KEY_BLUETOOTH": 237,
    "KEY_WLAN": 238, "KEY_UWB": 239, "KEY_UNKNOWN": 240,
    # Mouse buttons (also valid in bindings so a spare mouse can trigger macros)
    "BTN_LEFT": 0x110, "BTN_RIGHT": 0x111, "BTN_MIDDLE": 0x112, "BTN_SIDE": 0x113,
    "BTN_EXTRA": 0x114, "BTN_FORWARD": 0x115, "BTN_BACK": 0x116, "BTN_TASK": 0x117,
}

CODE_NAMES: dict[int, str] = {code: name for name, code in KEY_CODES.items()}

_K = KEY_CODES

EVDEV_TO_HID: dict[int, int] = {
    _K["KEY_A"]: 0x04, _K["KEY_B"]: 0x05, _K["KEY_C"]: 0x06, _K["KEY_D"]: 0x07,
    _K["KEY_E"]: 0x08, _K["KEY_F"]: 0x09, _K["KEY_G"]: 0x0A, _K["KEY_H"]: 0x0B,
    _K["KEY_I"]: 0x0C, _K["KEY_J"]: 0x0D, _K["KEY_K"]: 0x0E, _K["KEY_L"]: 0x0F,
    _K["KEY_M"]: 0x10, _K["KEY_N"]: 0x11, _K["KEY_O"]: 0x12, _K["KEY_P"]: 0x13,
    _K["KEY_Q"]: 0x14, _K["KEY_R"]: 0x15, _K["KEY_S"]: 0x16, _K["KEY_T"]: 0x17,
    _K["KEY_U"]: 0x18, _K["KEY_V"]: 0x19, _K["KEY_W"]: 0x1A, _K["KEY_X"]: 0x1B,
    _K["KEY_Y"]: 0x1C, _K["KEY_Z"]: 0x1D,
    _K["KEY_1"]: 0x1E, _K["KEY_2"]: 0x1F, _K["KEY_3"]: 0x20, _K["KEY_4"]: 0x21,
    _K["KEY_5"]: 0x22, _K["KEY_6"]: 0x23, _K["KEY_7"]: 0x24, _K["KEY_8"]: 0x25,
    _K["KEY_9"]: 0x26, _K["KEY_0"]: 0x27,
    _K["KEY_ENTER"]: 0x28, _K["KEY_ESC"]: 0x29, _K["KEY_BACKSPACE"]: 0x2A,
    _K["KEY_TAB"]: 0x2B, _K["KEY_SPACE"]: 0x2C, _K["KEY_MINUS"]: 0x2D,
    _K["KEY_EQUAL"]: 0x2E, _K["KEY_LEFTBRACE"]: 0x2F, _K["KEY_RIGHTBRACE"]: 0x30,
    _K["KEY_BACKSLASH"]: 0x31, _K["KEY_SEMICOLON"]: 0x33, _K["KEY_APOSTROPHE"]: 0x34,
    _K["KEY_GRAVE"]: 0x35, _K["KEY_COMMA"]: 0x36, _K["KEY_DOT"]: 0x37,
    _K["KEY_SLASH"]: 0x38, _K["KEY_CAPSLOCK"]: 0x39,
    _K["KEY_F1"]: 0x3A, _K["KEY_F2"]: 0x3B, _K["KEY_F3"]: 0x3C, _K["KEY_F4"]: 0x3D,
    _K["KEY_F5"]: 0x3E, _K["KEY_F6"]: 0x3F, _K["KEY_F7"]: 0x40, _K["KEY_F8"]: 0x41,
    _K["KEY_F9"]: 0x42, _K["KEY_F10"]: 0x43, _K["KEY_F11"]: 0x44, _K["KEY_F12"]: 0x45,
    _K["KEY_SYSRQ"]: 0x46, _K["KEY_SCROLLLOCK"]: 0x47, _K["KEY_PAUSE"]: 0x48,
    _K["KEY_INSERT"]: 0x49, _K["KEY_HOME"]: 0x4A, _K["KEY_PAGEUP"]: 0x4B,
    _K["KEY_DELETE"]: 0x4C, _K["KEY_END"]: 0x4D, _K["KEY_PAGEDOWN"]: 0x4E,
    _K["KEY_RIGHT"]: 0x4F, _K["KEY_LEFT"]: 0x50, _K["KEY_DOWN"]: 0x51, _K["KEY_UP"]: 0x52,
    _K["KEY_NUMLOCK"]: 0x53, _K["KEY_KPSLASH"]: 0x54, _K["KEY_KPASTERISK"]: 0x55,
    _K["KEY_KPMINUS"]: 0x56, _K["KEY_KPPLUS"]: 0x57, _K["KEY_KPENTER"]: 0x58,
    _K["KEY_KP1"]: 0x59, _K["KEY_KP2"]: 0x5A, _K["KEY_KP3"]: 0x5B, _K["KEY_KP4"]: 0x5C,
    _K["KEY_KP5"]: 0x5D, _K["KEY_KP6"]: 0x5E, _K["KEY_KP7"]: 0x5F, _K["KEY_KP8"]: 0x60,
    _K["KEY_KP9"]: 0x61, _K["KEY_KP0"]: 0x62, _K["KEY_KPDOT"]: 0x63,
    _K["KEY_102ND"]: 0x64, _K["KEY_COMPOSE"]: 0x65, _K["KEY_MENU"]: 0x65,
    _K["KEY_POWER"]: 0x66, _K["KEY_KPEQUAL"]: 0x67,
    _K["KEY_F13"]: 0x68, _K["KEY_F14"]: 0x69, _K["KEY_F15"]: 0x6A, _K["KEY_F16"]: 0x6B,
    _K["KEY_F17"]: 0x6C, _K["KEY_F18"]: 0x6D, _K["KEY_F19"]: 0x6E, _K["KEY_F20"]: 0x6F,
    _K["KEY_F21"]: 0x70, _K["KEY_F22"]: 0x71, _K["KEY_F23"]: 0x72, _K["KEY_F24"]: 0x73,
    _K["KEY_OPEN"]: 0x74, _K["KEY_HELP"]: 0x75, _K["KEY_PROPS"]: 0x76, _K["KEY_FRONT"]: 0x77,
    _K["KEY_STOP"]: 0x78, _K["KEY_AGAIN"]: 0x79, _K["KEY_UNDO"]: 0x7A, _K["KEY_CUT"]: 0x7B,
    _K["KEY_COPY"]: 0x7C, _K["KEY_PASTE"]: 0x7D, _K["KEY_FIND"]: 0x7E,
    _K["KEY_MUTE"]: 0x7F, _K["KEY_VOLUMEUP"]: 0x80, _K["KEY_VOLUMEDOWN"]: 0x81,
    _K["KEY_KPCOMMA"]: 0x85, _K["KEY_RO"]: 0x87, _K["KEY_KATAKANAHIRAGANA"]: 0x88,
    _K["KEY_YEN"]: 0x89, _K["KEY_HENKAN"]: 0x8A, _K["KEY_MUHENKAN"]: 0x8B,
    _K["KEY_KPJPCOMMA"]: 0x8C, _K["KEY_HANGEUL"]: 0x90, _K["KEY_HANJA"]: 0x91,
    _K["KEY_KATAKANA"]: 0x92, _K["KEY_HIRAGANA"]: 0x93, _K["KEY_ZENKAKUHANKAKU"]: 0x94,
    _K["KEY_KPLEFTPAREN"]: 0xB6, _K["KEY_KPRIGHTPAREN"]: 0xB7,
    _K["KEY_LEFTCTRL"]: 0xE0, _K["KEY_LEFTSHIFT"]: 0xE1, _K["KEY_LEFTALT"]: 0xE2,
    _K["KEY_LEFTMETA"]: 0xE3, _K["KEY_RIGHTCTRL"]: 0xE4, _K["KEY_RIGHTSHIFT"]: 0xE5,
    _K["KEY_RIGHTALT"]: 0xE6, _K["KEY_RIGHTMETA"]: 0xE7,
}

HID_TO_EVDEV: dict[int, int] = {}
for _code, _usage in EVDEV_TO_HID.items():
    # keep the first (canonical) evdev code for each usage
    HID_TO_EVDEV.setdefault(_usage, _code)

MODIFIER_MIN = 0xE0
MODIFIER_MAX = 0xE7

# Boot-protocol descriptor covers array usages 0x00..0x65 only.
BOOT_DESCRIPTOR_MAX_USAGE = 0x65


def is_modifier(usage: int) -> bool:
    return MODIFIER_MIN <= usage <= MODIFIER_MAX


# ----------------------------------------------------------------------------
# Friendly key names for macro definitions
# ----------------------------------------------------------------------------
KEY_ALIASES: dict[str, int] = {
    # modifiers
    "ctrl": 0xE0, "control": 0xE0, "lctrl": 0xE0, "leftctrl": 0xE0,
    "shift": 0xE1, "lshift": 0xE1, "leftshift": 0xE1,
    "alt": 0xE2, "lalt": 0xE2, "leftalt": 0xE2, "option": 0xE2,
    "meta": 0xE3, "win": 0xE3, "windows": 0xE3, "super": 0xE3, "gui": 0xE3,
    "cmd": 0xE3, "lmeta": 0xE3, "lwin": 0xE3,
    "rctrl": 0xE4, "rightctrl": 0xE4,
    "rshift": 0xE5, "rightshift": 0xE5,
    "ralt": 0xE6, "rightalt": 0xE6, "altgr": 0xE6,
    "rmeta": 0xE7, "rwin": 0xE7, "rightmeta": 0xE7,
    # editing / navigation
    "enter": 0x28, "return": 0x28, "esc": 0x29, "escape": 0x29,
    "backspace": 0x2A, "bksp": 0x2A, "tab": 0x2B, "space": 0x2C,
    "minus": 0x2D, "dash": 0x2D, "equal": 0x2E, "equals": 0x2E,
    "leftbrace": 0x2F, "lbracket": 0x2F, "rightbrace": 0x30, "rbracket": 0x30,
    "backslash": 0x31, "semicolon": 0x33, "apostrophe": 0x34, "quote": 0x34,
    "grave": 0x35, "backtick": 0x35, "comma": 0x36, "period": 0x37, "dot": 0x37,
    "slash": 0x38, "capslock": 0x39, "caps": 0x39,
    "printscreen": 0x46, "prtsc": 0x46, "sysrq": 0x46, "scrolllock": 0x47,
    "pause": 0x48, "break": 0x48, "insert": 0x49, "ins": 0x49, "home": 0x4A,
    "pageup": 0x4B, "pgup": 0x4B, "delete": 0x4C, "del": 0x4C, "end": 0x4D,
    "pagedown": 0x4E, "pgdn": 0x4E, "right": 0x4F, "left": 0x50, "down": 0x51, "up": 0x52,
    "numlock": 0x53, "kpslash": 0x54, "kpdivide": 0x54, "kpasterisk": 0x55,
    "kpmultiply": 0x55, "kpminus": 0x56, "kpplus": 0x57, "kpenter": 0x58,
    "kp1": 0x59, "kp2": 0x5A, "kp3": 0x5B, "kp4": 0x5C, "kp5": 0x5D, "kp6": 0x5E,
    "kp7": 0x5F, "kp8": 0x60, "kp9": 0x61, "kp0": 0x62, "kpdot": 0x63, "kpperiod": 0x63,
    "menu": 0x65, "app": 0x65, "application": 0x65, "compose": 0x65,
    "power": 0x66, "kpequal": 0x67, "mute": 0x7F, "volumeup": 0x80, "volumedown": 0x81,
    "plus": 0x2E,  # shifted '=' - handled by macros when typing; bare key is '='
}
for _i in range(1, 25):
    KEY_ALIASES[f"f{_i}"] = 0x3A + (_i - 1) if _i <= 12 else 0x68 + (_i - 13)
for _i, _ch in enumerate("abcdefghijklmnopqrstuvwxyz"):
    KEY_ALIASES[_ch] = 0x04 + _i
for _i, _ch in enumerate("1234567890"):
    KEY_ALIASES[_ch] = 0x1E + _i


def usage_from_name(name: str) -> int:
    """Resolve a key name (alias, KEY_* evdev name or 0xNN usage) to a HID usage."""
    raw = name.strip()
    if not raw:
        raise KeyError("empty key name")
    low = raw.lower()
    if low in KEY_ALIASES:
        return KEY_ALIASES[low]
    upper = raw.upper()
    if upper in KEY_CODES:
        code = KEY_CODES[upper]
        if code in EVDEV_TO_HID:
            return EVDEV_TO_HID[code]
        raise KeyError(f"{raw} has no HID keyboard usage")
    if low.startswith("0x"):
        value = int(low, 16)
        if 0 < value <= 0xFF:
            return value
    raise KeyError(f"unknown key name: {raw}")


# ----------------------------------------------------------------------------
# US QWERTY layout for text typing: char -> (usage, shift)
# ----------------------------------------------------------------------------
US_LAYOUT: dict[str, tuple[int, bool]] = {}
for _i, _ch in enumerate("abcdefghijklmnopqrstuvwxyz"):
    US_LAYOUT[_ch] = (0x04 + _i, False)
    US_LAYOUT[_ch.upper()] = (0x04 + _i, True)
for _i, _ch in enumerate("1234567890"):
    US_LAYOUT[_ch] = (0x1E + _i, False)
for _i, _ch in enumerate("!@#$%^&*()"):
    US_LAYOUT[_ch] = (0x1E + _i, True)
US_LAYOUT.update({
    "\n": (0x28, False), "\r": (0x28, False), "\t": (0x2B, False), " ": (0x2C, False),
    "-": (0x2D, False), "_": (0x2D, True), "=": (0x2E, False), "+": (0x2E, True),
    "[": (0x2F, False), "{": (0x2F, True), "]": (0x30, False), "}": (0x30, True),
    "\\": (0x31, False), "|": (0x31, True), ";": (0x33, False), ":": (0x33, True),
    "'": (0x34, False), '"': (0x34, True), "`": (0x35, False), "~": (0x35, True),
    ",": (0x36, False), "<": (0x36, True), ".": (0x37, False), ">": (0x37, True),
    "/": (0x38, False), "?": (0x38, True),
})

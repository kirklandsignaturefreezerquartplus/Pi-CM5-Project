"""Configuration loading (TOML, standard library ``tomllib``)."""
from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass, field
from typing import Any

DEFAULT_CONFIG_PATH = "/etc/hid-bridge/config.toml"


class ConfigError(Exception):
    pass


@dataclass
class GadgetConfig:
    name: str = "hidbridge"
    vendor_id: int = 0x1209
    product_id: int = 0x0001
    device_version: int = 0x0100
    manufacturer: str = "Generic"
    product: str = "USB Keyboard"
    serial: str = ""
    max_speed: str = "full-speed"
    self_powered: bool = False
    remote_wakeup: bool = True
    max_power_ma: int = 100
    udc: str = ""
    configfs: str = "/sys/kernel/config/usb_gadget"


@dataclass
class KeyboardConfig:
    descriptor: str = "boot"  # boot | extended
    poll_interval_ms: int = 10


@dataclass
class MouseConfig:
    mode: str = "relative"  # relative | absolute
    buttons: int = 3
    poll_interval_ms: int = 2
    # Used when converting an absolute source (PiKVM absolute mode) to relative
    # output: the source range is mapped onto this many "pixels".
    abs_to_rel_resolution: tuple[int, int] = (1920, 1080)
    # Used when converting a relative source to absolute output: how many
    # absolute units (0..32767) one relative count moves the virtual cursor.
    rel_to_abs_gain: float = 17.0


@dataclass
class BridgeConfig:
    grab_inputs: bool = True
    rescan_interval_ms: int = 1000
    tap_ms: int = 30
    step_ms: int = 20
    write_timeout_ms: int = 50
    forward_leds: bool = True
    control_socket: str = "/run/hid-bridge/ctl.sock"
    log_level: str = "info"


@dataclass
class InputRule:
    name: str | None = None      # regex matched against the evdev device name
    phys: str | None = None      # regex matched against the physical path
    vendor: int | None = None
    product: int | None = None
    role: str = "passthrough"    # passthrough | macro | ignore
    grab: bool | None = None     # None -> bridge.grab_inputs
    unbound: str = "drop"        # for role=macro: drop | passthrough
    bindings: dict[str, str] = field(default_factory=dict)
    label: str = ""

    def matches(self, name: str, phys: str, vendor: int, product: int) -> bool:
        if self.name is not None and not re.search(self.name, name):
            return False
        if self.phys is not None and not re.search(self.phys, phys):
            return False
        if self.vendor is not None and self.vendor != vendor:
            return False
        if self.product is not None and self.product != product:
            return False
        return True

    def describe(self) -> str:
        if self.label:
            return self.label
        parts = []
        if self.name is not None:
            parts.append(f"name~{self.name!r}")
        if self.phys is not None:
            parts.append(f"phys~{self.phys!r}")
        if self.vendor is not None:
            parts.append(f"vendor={self.vendor:04x}")
        if self.product is not None:
            parts.append(f"product={self.product:04x}")
        return " ".join(parts) or "<any>"


@dataclass
class Config:
    gadget: GadgetConfig = field(default_factory=GadgetConfig)
    keyboard: KeyboardConfig = field(default_factory=KeyboardConfig)
    mouse: MouseConfig = field(default_factory=MouseConfig)
    bridge: BridgeConfig = field(default_factory=BridgeConfig)
    inputs: list[InputRule] = field(default_factory=list)
    macros: dict[str, list[str]] = field(default_factory=dict)
    path: str = ""

    def rule_for(self, name: str, phys: str, vendor: int, product: int) -> InputRule:
        for rule in self.inputs:
            if rule.matches(name, phys, vendor, product):
                return rule
        return InputRule(label="default passthrough")


def _int(value: Any, what: str) -> int:
    if isinstance(value, bool):
        raise ConfigError(f"{what}: expected an integer, got a boolean")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    raise ConfigError(f"{what}: expected an integer (decimal or 0x hex), got {value!r}")


def _apply(section: dict[str, Any], target: Any, what: str, int_fields: set[str]) -> None:
    for key, value in section.items():
        if not hasattr(target, key):
            raise ConfigError(f"{what}: unknown option {key!r}")
        if key in int_fields:
            value = _int(value, f"{what}.{key}")
        setattr(target, key, value)


def parse_config(data: dict[str, Any], path: str = "") -> Config:
    cfg = Config(path=path)
    known = {"gadget", "keyboard", "mouse", "bridge", "inputs", "macros"}
    unknown = set(data) - known
    if unknown:
        raise ConfigError(f"unknown top-level section(s): {', '.join(sorted(unknown))}")

    _apply(data.get("gadget", {}), cfg.gadget, "gadget",
           {"vendor_id", "product_id", "device_version", "max_power_ma"})
    _apply(data.get("keyboard", {}), cfg.keyboard, "keyboard", {"poll_interval_ms"})
    mouse = dict(data.get("mouse", {}))
    if "abs_to_rel_resolution" in mouse:
        res = mouse.pop("abs_to_rel_resolution")
        if not (isinstance(res, list) and len(res) == 2):
            raise ConfigError("mouse.abs_to_rel_resolution must be [width, height]")
        cfg.mouse.abs_to_rel_resolution = (_int(res[0], "width"), _int(res[1], "height"))
    _apply(mouse, cfg.mouse, "mouse", {"buttons", "poll_interval_ms"})
    _apply(data.get("bridge", {}), cfg.bridge, "bridge",
           {"rescan_interval_ms", "tap_ms", "step_ms", "write_timeout_ms"})

    for index, raw in enumerate(data.get("inputs", [])):
        if not isinstance(raw, dict):
            raise ConfigError(f"inputs[{index}] must be a table")
        rule = InputRule()
        for key, value in raw.items():
            if key in ("vendor", "product"):
                setattr(rule, key, _int(value, f"inputs[{index}].{key}"))
            elif key == "bindings":
                if not isinstance(value, dict):
                    raise ConfigError(f"inputs[{index}].bindings must be a table")
                rule.bindings = {str(k).upper(): str(v) for k, v in value.items()}
            elif hasattr(rule, key):
                setattr(rule, key, value)
            else:
                raise ConfigError(f"inputs[{index}]: unknown option {key!r}")
        if rule.role not in ("passthrough", "macro", "ignore"):
            raise ConfigError(f"inputs[{index}].role must be passthrough, macro or ignore")
        if rule.unbound not in ("drop", "passthrough"):
            raise ConfigError(f"inputs[{index}].unbound must be drop or passthrough")
        for pattern_key in ("name", "phys"):
            pattern = getattr(rule, pattern_key)
            if pattern is not None:
                try:
                    re.compile(pattern)
                except re.error as exc:
                    raise ConfigError(f"inputs[{index}].{pattern_key}: bad regex: {exc}") from exc
        cfg.inputs.append(rule)

    macros = data.get("macros", {})
    if not isinstance(macros, dict):
        raise ConfigError("macros must be a table of name = [steps]")
    for name, steps in macros.items():
        if isinstance(steps, str):
            steps = [steps]
        if not isinstance(steps, list) or not all(isinstance(s, str) for s in steps):
            raise ConfigError(f"macros.{name} must be a string or an array of step strings")
        cfg.macros[str(name)] = list(steps)

    validate(cfg)
    return cfg


def validate(cfg: Config) -> None:
    g = cfg.gadget
    for label, value in (("vendor_id", g.vendor_id), ("product_id", g.product_id),
                         ("device_version", g.device_version)):
        if not 0 <= value <= 0xFFFF:
            raise ConfigError(f"gadget.{label} must be within 0x0000-0xFFFF")
    if g.max_speed not in ("low-speed", "full-speed", "high-speed"):
        raise ConfigError("gadget.max_speed must be low-speed, full-speed or high-speed")
    if not 0 < g.max_power_ma <= 500:
        raise ConfigError("gadget.max_power_ma must be within 1-500")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", g.name):
        raise ConfigError("gadget.name may only contain letters, digits, '_', '.' and '-'")
    if cfg.keyboard.descriptor not in ("boot", "extended"):
        raise ConfigError("keyboard.descriptor must be boot or extended")
    if cfg.mouse.mode not in ("relative", "absolute"):
        raise ConfigError("mouse.mode must be relative or absolute")
    if cfg.mouse.buttons not in (3, 5):
        raise ConfigError("mouse.buttons must be 3 or 5")
    for label, value in (("keyboard.poll_interval_ms", cfg.keyboard.poll_interval_ms),
                         ("mouse.poll_interval_ms", cfg.mouse.poll_interval_ms)):
        if not 1 <= value <= 255:
            raise ConfigError(f"{label} must be within 1-255")
    if cfg.bridge.log_level.upper() not in ("DEBUG", "INFO", "WARNING", "ERROR"):
        raise ConfigError("bridge.log_level must be debug, info, warning or error")
    for rule in cfg.inputs:
        for key, macro in rule.bindings.items():
            if macro not in cfg.macros:
                raise ConfigError(f"binding {key} -> {macro!r}: no such macro")
    # Validate macro step syntax early so a typo fails at start-up, not mid-run.
    from . import macros as macro_module
    for name, steps in cfg.macros.items():
        for step in steps:
            try:
                macro_module.parse_step(step, cfg.macros)
            except macro_module.MacroError as exc:
                raise ConfigError(f"macros.{name}: {exc}") from exc


def load_config(path: str | None = None) -> Config:
    path = path or os.environ.get("HID_BRIDGE_CONFIG", DEFAULT_CONFIG_PATH)
    try:
        with open(path, "rb") as fh:
            data = tomllib.load(fh)
    except FileNotFoundError:
        raise ConfigError(f"config file not found: {path}")
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path}: {exc}")
    return parse_config(data, path)

# Analysis of the external AI code review

An AI code-review tool produced ten findings against this project.  It had
access to three files only: `config/config.toml`, `hid_bridge/gadget.py` and
`docs/remaining-tells.md`.  It did not see `hidg.py`, `bridge.py`, the kernel
patches, `docs/usb-identity.md`, or the kernel sources.  Each finding below is
checked against the actual code and against the Raspberry Pi `rpi-6.12.y`
kernel sources (`drivers/usb/gadget/composite.c`, `configfs.c`,
`function/f_hid.c`, `drivers/usb/dwc2/gadget.c`, `core_intr.c`, `params.c`).
Line numbers refer to those unpatched files.

## Summary

| # | Review item | Claim | Proposed fix | What we did |
|---|---|---|---|---|
| 1 | VBUS current & suspend | restates `remaining-tells.md` §2 | same as ours | corrected the sysfs path we had given for the suspend state |
| 2 | Boot ROM & enumeration timing | restates §4/§5 | same as ours | corrected our own "12 V" wording (the CM5 IO Board has no DC jack) |
| 3 | Hardcoded bcdUSB / bMaxPacketSize0 | tell is real, mechanism wrong | **ineffective**: the kernel overwrites both regardless of configfs | documented; a kernel patch is the only route (offered as 0005) |
| 4 | Interface topology & endpoints | premise backwards on OUT endpoints; underlying cloning gap real | over-scoped rewrite | identity tool now diffs the reference's descriptor tree and warns |
| 5 | Remote wakeup | restates §3 / patch 0004 | same as ours | none; the review omits that 0004 is untested on hardware |
| 6 | ConfigFS / f_hid quirks | true in theory, misframed | raw-gadget "custom kernel driver" | not recommended; explained |
| 7 | DWC2 fingerprinting / MCU proxy | justification weak, conclusion strong for other reasons | RP2040 front-end | recommended as the strategic option, with a concrete design |
| 8 | Macro jitter | wrong USB mechanics | kernel module / RTOS | not needed; already handled at the scale that matters |
| 9 | Write-timeout backpressure | mis-stated, but hid a real bug | wrong model (ring buffer) | **fixed**: latest-state model, never blocks, no stuck keys |
| 10 | Mouse quantization | no floating-point aliasing; non-default mode | dithering / 1:1 | 1:1 is already the default; low priority |

Net: three items restate our own residual-tells document, one is factually
wrong about what configfs can do, two are theoretically valid but propose
disproportionate fixes with the wrong justification, two misunderstand USB
interrupt transfers, and two point (with backwards or mis-stated premises) at
real gaps that are now closed.  Reviewing the review also surfaced two
inaccuracies in our own docs, both fixed.

## Item by item

### 1. VBUS current and suspend current

**Claim.** Correct, and identical to `remaining-tells.md` §2 including both
suggested mitigations (resistive load; GPIO-switched load driven by the
suspend state).  Nothing new.

**Correction to our doc.** We had written that `cdev->suspended` is exported
at `/sys/class/udc/*/device/suspended`.  libcomposite creates the attribute
on the *gadget* device (`composite.c:2448`, `device_create_file(&gadget->dev,
&dev_attr_suspended)`), which the UDC core names `gadget.N` under the
controller device (`core.c:1453`), while the `/sys/class/udc/<udc>` link
points at the controller (`core.c:1417-1419`).  The path is therefore
`/sys/class/udc/<udc>/device/gadget.0/suspended`.  Fixed.

### 2. Boot ROM fallback and enumeration timing

**Claim.** Correct and identical to `remaining-tells.md` §4/§5.  The "12 V"
in the review's fix was copied from our own §4, written before we corrected
`hardware.md`: the official CM5 IO Board takes power only through USB-C PD
or the PoE+ HAT (or a 5 V feed on the header), there is no DC jack.  §4 now
says so.

### 3. "Hardcoded" bcdUSB and bMaxPacketSize0

**Claim.** The tell is real (a cloned USB 1.1 keyboard reports bcdUSB 1.10
and an 8-byte EP0; we report 2.00 and 64) and was already listed in
`docs/usb-identity.md` as kernel-fixed.

**Proposed fix is ineffective.** The review suggests parsing both values
from the `lsusb` dump into configfs instead of "hardcoding" them.  The
kernel ignores what configfs holds for these two fields when it answers
`GET_DESCRIPTOR(DEVICE)`:

* `composite.c:1830-1845` (`composite_setup`, `case USB_DT_DEVICE`) sets
  `cdev->desc.bMaxPacketSize0 = cdev->gadget->ep0->maxpacket` and then
  recomputes `bcdUSB` from the gadget's capabilities (0x0200, or 0x0201 with
  LPM, 0x0210/0x0320 for SuperSpeed).  The configfs store
  (`configfs.c:225-238`) writes `cdev.desc.bcdUSB`, but that value is
  overwritten at request time.
* dwc2 fixes EP0 at 64 bytes for full and high speed
  (`gadget.c`, `dwc2_hsotg_irq_enumdone`: `ep0_mps = EP0_MPS_LIMIT` for
  `DSTS_ENUMSPD_FS`/`HS`; `core.h: EP0_MPS_LIMIT 64`); only low speed uses 8.

`gadget.py` writes 0x0200 and 0x40 deliberately so that the configfs tree
shows what is on the wire; the comment in the code says so.  Parsing other
values in would change nothing except make configfs lie.

**What would work.** A kernel patch, which is feasible because the hardware
already supports an 8-byte EP0 (the low-speed path uses it):

1. dwc2: at full speed, use an EP0 packet size of 8 when requested (a DT or
   module parameter, or honour a lowered `ep0->maxpacket_limit`), instead of
   always `EP0_MPS_LIMIT`.  composite then reports 8 automatically since it
   copies `ep0->maxpacket`.
2. composite: when the driver is limited to full speed (which patch 0002
   already uses to suppress the qualifier and LPM), honour the configfs
   `bcdUSB` (1.10) instead of forcing 2.00.

About 20 lines, untested like 0004.  Trade-off: an 8-byte EP0 makes
enumeration take eight times as many control packets, exactly as a USB 1.1
keyboard does; no functional impact.  We can add this as patch 0005 on
request; it only matters when cloning a USB 1.1 reference.

### 4. Interface topology and endpoints

**Premise is backwards.** The review calls the absence of an interrupt OUT
endpoint a tell.  The common design for boot keyboards is exactly one
interrupt IN endpoint with LEDs delivered by `SET_REPORT` on the control
endpoint; an interrupt OUT endpoint is the less common variant.
`no_out_endpoint = 1` therefore matches the typical device, and
`usb_f_hid` supports both (`f_hid.c: use_out_ep`).

**Underlying gap is real.** `tools/identity-from-lsusb.py` cloned VID/PID,
strings and power attributes but said nothing when the reference device's
descriptor *tree* differs from what hid-bridge presents: number of
interfaces (many keyboards have a third, consumer-control interface with
subclass 0/protocol 0), endpoint count, `bInterval`, `wMaxPacketSize`,
`bcdHID`, and the report-descriptor length (a Logitech K120, for instance,
has a 65-byte keyboard descriptor and a 159-byte second interface, not our
63 and 52).  An inspector comparing a cloned VID:PID against a known dump of
that model would see every one of those.

**Fix applied (commit 815bc38).** The tool now parses the reference's
interface, HID and endpoint descriptors and prints a `# WARNING:` line for
each difference, ending with advice to choose a reference with matching
topology.  A "clone mode" that loads report descriptors from files, adds a
consumer-control interface or enables the OUT endpoint per interface is a
possible follow-up; `usb_f_hid` can vary subclass, protocol, report length,
descriptor bytes and the OUT endpoint per function, but not `bInterval`
(`f_hid.c:263,275`, fixed at 10 ms full-speed) or `bcdHID`
(`f_hid.c:145`).  "Rewrite the initialization logic to dynamically construct
interfaces" is the right direction stated as a much larger job than needed.

### 5. Remote wakeup

**Claim.** Correct and identical to `remaining-tells.md` §3 and
`kernel-patches/0004`.  The review omits the material caveat: 0004 applies
cleanly but has not been exercised on hardware.  dwc2 has every register
piece (`gadget.c`, `dwc2_gadget_exit_clock_gating` sets
`DCTL_RMTWKUPSIG`; `core_intr.c`, `dwc2_handle_wakeup_detected_intr`) but
no gadget `.wakeup` operation; 0004 adds it.

### 6. ConfigFS / f_hid "state quirks"

**Claim, checked.** For an invalid string index libcomposite's `get_string`
returns `-EINVAL` (`composite.c:1316`, via `usbstring.c:54`), `composite_setup`
returns the negative value (`composite.c:2308-2309`) and dwc2 stalls EP0
(`gadget.c:2000-2001`, `dwc2_hsotg_stall_ep0`).  Unknown requests take the
same path from the `-EOPNOTSUPP` default (`composite.c:1782`).  That is the
behaviour USB 2.0 §9.2.7 requires of every device, and what the large
majority of keyboard firmware does.

**Framing.** The review's mitigation, emulating a specific ASIC's crash or
garbage responses, is (a) contrary to the project goal of a *generic,
compliant* keyboard, (b) not achievable without first fuzzing the physical
reference device with an analyser to learn its quirks, and (c) misdescribed:
raw-gadget is a user-space interface (`/dev/raw-gadget`), not a custom kernel
driver.  Device fingerprinting from enumeration behaviour and timing exists
in the research literature, but it needs a per-model baseline; no host
software does this.  Not recommended.

### 7. DWC2 controller fingerprinting and the MCU proxy

**Justification is weak.** An RP2040 has its own electrical and timing
signature; it only "matches the cloned target's cheap controller" if it is
that controller.  Nothing about the dwc2 core's behaviour on edge-case
packets is documented as distinguishable by any host in practice.

**Conclusion is nevertheless the strongest option, for other reasons.** A
small MCU USB front-end (RP2040 with TinyUSB, driven by the CM5 over UART)
would close, without any kernel patch, every item that is hard for the
gadget stack:

* bus-powered from the target, so idle and suspend current are *real*
  (`remaining-tells.md` §2 solved outright, including the GPIO-load idea);
* enumerates within milliseconds of the port powering up, independent of
  the CM5's boot (§4), and the CM5's own USB-C never touches the target, so
  the boot-ROM fallback cannot be seen there (§5);
* every descriptor byte under firmware control: bcdUSB 1.10, EP0 8, bcdHID
  1.10, exact report descriptors, any interface topology (items 3 and 4);
* real remote wakeup through TinyUSB (item 5), no dwc2 patch;
* reports paced by the MCU at the poll rate regardless of Python timing.

PiKVM's own Pico HID (RP2040 + TinyUSB) is prior art.  The bridge already
isolates its output behind one class (`hid_bridge/hidg.py: HidgDevice`, with
`write_report`, `read_output_report`, `poll_readable`, `host_state_changed`
and an `fd`), so a serial sink is a sibling class plus a config switch, not
a rewrite.  Cost: a few hundred lines of firmware, a UART link, and losing
the "pure CM5" simplicity.  This is the recommended path if the remaining
hardware tells matter; otherwise the current design with the five kernel
patches is complete.

### 8. Macro jitter and "microsecond timing"

**Wrong mechanics.** A host cannot measure when user space wrote a report.
It polls the interrupt IN endpoint at `bInterval` and receives whatever
report is waiting: `f_hid.c` fixes that at 10 ms for full speed
(`hidg_fs_in_ep_desc.bInterval = 10`, lines 263/275) and 1 ms at high speed
(`bInterval = 4`, lines 160/181), and it keeps exactly one request in flight
(`write_pending`).  Every observation the host can make is therefore
quantized to the polling interval.  Sub-millisecond scheduler or garbage
collection jitter disappears at 10 ms quantization and shifts at most one
1 ms slot at high speed, which is indistinguishable from any device.

What *is* observable is the cadence in poll units (a fixed 30 ms tap is
always three polls), and `bridge.macro_jitter_ms` already randomizes it
(`macros.py: MacroEngine.tap_delay/gap_delay`).  A kernel module or
real-time proxy would change nothing the host can see.

### 9. Write-timeout backpressure

**Mis-stated in two ways.** Nothing "dropped the connection": after 50 ms of
the previous report not being collected, one *report* was dropped.  And a
hardware "ring buffer overwriting the oldest packet" is the wrong model for
HID: a real keyboard or mouse has one report register; the latest state
wins and motion counts accumulate between polls.

**But the item concealed a real defect.** With `usb_f_hid`'s single in-flight
request (`f_hid.c: f_hidg_write`, `WRITE_COND (!hidg->write_pending)`,
`-EAGAIN` with `O_NONBLOCK`; cleared in the completion handler at line 461
and in `hidg_set_alt` at 1119), the old `hidg.py` (a) blocked the whole
single-threaded loop for up to 50 ms on every second report written within
one poll interval, which any mouse stream above 100 Hz triggers, and (b) if
the host stopped polling for longer than 50 ms, a key-down could stay in
flight while the matching key-up was dropped; when polling resumed the host
received the key-down and nothing else: a stuck key with autorepeat until
the next state change.

**Fix applied (commit 815bc38).** The bridge now holds "what the host should
receive next" per interface: the keyboard report is recomputed from the
merged key state at flush time, relative motion accumulates with saturation
like a mouse's counters, absolute mode keeps the latest position, and
pending state is flushed when `select()` reports the hidg fd writable
(`f_hidg_poll` sets `EPOLLOUT` once `write_pending` clears).  No call blocks,
no state change is lost, idle mouse reports are not repeated, and the
current state is re-sent when the host comes back.  Six new tests cover the
stall scenarios; `write_timeout_ms` is gone.

### 10. Mouse quantization

**Checked.** `rel_to_abs_gain` is used only in relative-source →
absolute-output conversion (`bridge.py: _emit_mouse_motion`, non-default),
where `round(dx * 17.0)` with integer `dx` produces exact multiples of 17;
17.0 is exactly representable, so there is no floating-point aliasing, just a
17-unit position step in a mode that is not recommended.  The default path
(relative in, relative out) passes integer deltas through 1:1, which is the
review's own recommended fix.  Absolute-in → relative-out uses `scale_abs`
(`reports.py`) onto a virtual 1920×1080 screen, producing integer pixel
deltas like any mouse.  Low priority; an integer gain with optional dither
could be added for the rel→abs mode if someone uses it.

## Changes made because of this analysis

* `815bc38` latest-state report model (item 9); identity tool topology
  warnings (item 4); doc corrections (items 1 and 2).
* This document.

## Independent verification (added after the analysis above)

The ten verdicts were handed to independent verifier agents with the
repository and the kernel sources, and each verdict was then attacked by
two adversarial reviewers (a USB-protocol lens and a Linux-gadget-stack
lens).  Two completeness critics searched the whole project for anything
both the review and the analysis had missed.

**Verdicts.** All ten conclusions held.  Five were marked "materially
incomplete" on specific points, all folded in:

* Item 3: the only workable route to a USB 1.1 clone is lowering dwc2's
  EP0 size and stashing the configfs `bcdUSB` at bind; honouring
  `bMaxPacketSize0` from configfs (as `usb-identity.md` once suggested)
  would advertise a size the controller does not use.
* Item 4: `usb_f_hid` also attaches an interface string ("HID Interface")
  to every interface, a Linux-only tell nobody had listed.  Fixed in
  `kernel-patches/0001`.
* Item 5: the partial-power-down branch of patch 0004 never asserted the
  wakeup signal, the patch dereferenced the composite device before
  checking the function was configured, and it could drive resume inside
  the 5 ms minimum suspend time.  All three fixed in the reworked 0004.
* Item 6: `GET_REPORT` for an undeclared report ID was answered after a
  2.5 s stall with zeros, a timing signature.  Fixed in the reworked 0003.
* Item 7: an RP2040 front-end would not give an 8-byte EP0 out of the box
  (TinyUSB opens EP0 at 64) and the bridge's poll-paced output already
  matches an MCU's; the remaining benefits stand.

**Critics.** The robustness critic found one serious defect in the
latest-state refactor of commit 815bc38: when the host suspends the bus,
dwc2 refuses every queued request with EAGAIN while `poll()` still reports
the fd writable, so the loop would have spun at 100 % CPU with any pending
input until the host resumed.  The bridge now recognises "writable but
refused" as suspension, backs off exponentially, consults libcomposite's
`suspended` attribute before retrying, discards motion made while asleep,
and re-sends the current state on resume.  Also fixed from the same
report: a press-and-release inside one poll interval was coalesced away
(transitions are now queued and replayed in order); motion accumulated
during a long stall replayed as a multi-second cursor burst (it now
saturates to one 8-bit report like a real mouse); the bridge kept stale
`/dev/hidg*` descriptors after a gadget rebuild (they are revalidated every
second); a restart within one poll of a key-down could leave the key
auto-repeating (shutdown now waits briefly for the release to be
collected, and only when something was held); evdev `SYN_DROPPED` was
ignored (state is rebuilt from `EVIOCGKEY`); a control client that connected
without sending could stall the loop for 0.5 s (now 50 ms); a device
reusing an ignored `eventN` path inherited the old verdict (the inode is
tracked); and the mouse re-sync after a host reset was a no-op.

The protocol critic listed the residual request-level tells now closed by
`kernel-patches/0005` (self-powered before configuration, remote-wakeup
feature ACKed without the bit, test modes at full speed, `GET_STATUS` for a
non-existent interface), the mouse interface accepting `SET_REPORT(Output)`
(0003), LPM still enabled in the core after 0002 (0002 now turns it off),
unsolicited zero reports at bridge start and stop (removed), macro
modifiers landing in the same report as the key (they now lead and lag in
their own reports), and the D+ pull-up being present without VBUS
(`remaining-tells.md` §6).  Its remaining low items, `GET_IDLE` default 0
versus the recommended 500 ms and the exact host-side polling period, are
documented as deviations.

One more bus-level finding came out of checking the jitter refutation:
`f_hidg_write` queues every report with zero-length-packet termination, and
because the endpoint size equals the report length, every report is
followed by an empty packet on the next IN token.  No real HID device does
that, an analyser sees it on every keystroke, and it halves the achievable
report rate (one report per two polls).  Fixed in `kernel-patches/0001`.

Corrections to the earlier text of this document: the invalid-string-index
return is `composite.c:1367` (via `usbstring.c:55`), not 1316; the
high-speed `bInterval` constants are `f_hid.c:222/234`, not 160/181;
`raw_gadget` is itself a small kernel module that forwards every SETUP to
user space, so "a custom kernel driver using raw-gadget" is a contradiction
rather than merely imprecise; and "what most firmware does" and "no host
software does this" are general knowledge, not verifiable from the sources.

## Offered follow-ups

* Kernel patch 0005 (bcdUSB 1.10 and 8-byte EP0 at full speed) for cloning
  USB 1.1 references (item 3).
* A clone mode for report descriptors and extra interfaces (item 4).
* An RP2040 USB front-end with a serial sink in the bridge (item 7), the
  option that retires the hardware tells wholesale.

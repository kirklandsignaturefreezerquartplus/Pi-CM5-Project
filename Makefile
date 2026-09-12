PYTHON ?= python3

.PHONY: test check install uninstall lint

test:
	$(PYTHON) -m unittest discover -s tests -v

check:
	HID_BRIDGE_CONFIG=config/config.toml $(PYTHON) -m hid_bridge check

lint:
	$(PYTHON) -m pyflakes hid_bridge tests 2>/dev/null || $(PYTHON) -m compileall -q hid_bridge tests

install:
	sudo ./install.sh

uninstall:
	sudo ./uninstall.sh

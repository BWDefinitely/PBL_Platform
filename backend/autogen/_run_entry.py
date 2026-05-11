"""Subprocess entrypoint used by the API to launch autogen runs.

Installs a logging filter that suppresses the noisy
`Model ... is not found. The cost will be 0.` warning emitted by
`autogen.oai.client` whenever a non-OpenAI / proxy model name is used.
The warning is harmless (it only affects AutoGen's internal cost
estimator), but it pollutes the dialogue dataset logs.

Usage: python _run_entry.py <script> [args...]
"""

from __future__ import annotations

import logging
import runpy
import sys


class _DropPricingWarning(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        msg = record.getMessage()
        if "is not found. The cost will be 0" in msg:
            return False
        return True


def _install_filter() -> None:
    flt = _DropPricingWarning()
    # Attach to the specific logger AutoGen uses, plus root for safety.
    for name in ("autogen.oai.client", "autogen", ""):
        logging.getLogger(name).addFilter(flt)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python _run_entry.py <script> [args...]", file=sys.stderr)
        return 2
    _install_filter()
    target = sys.argv[1]
    # Shift argv so the target script sees its own args at argv[0..].
    sys.argv = sys.argv[1:]
    runpy.run_path(target, run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

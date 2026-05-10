"""Windows executable entrypoint for packaged QR Watch builds."""

from __future__ import annotations

import sys
from typing import Sequence

from qrwatch.cli import main as cli_main


def main(argv: Sequence[str] | None = None) -> int:
    """Run the packaged app with tray and local config defaults."""

    args = sys.argv[1:] if argv is None else list(argv)
    return cli_main(
        args,
        use_default_config_file=True,
        create_default_config=True,
        default_tray=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())

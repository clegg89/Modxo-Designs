#!/usr/bin/env python3
"""replace_modxo.py - replace the Modxo firmware region in a combined PrometheOS image"""

import argparse
import os
import sys

MODXO_SIZE = 256 * 1024  # 0x40000, size of the Modxo region
PAD_BYTE = b"\x00"       # use b"\xff" for erased-flash style padding


class Parser(argparse.ArgumentParser):
    """Print the error plus full usage and exit 1 on bad arguments."""

    def error(self, message):
        die(message, self)


def die(message, parser=None):
    print(f"Error: {message}\n", file=sys.stderr)
    (parser or build_parser()).print_help(sys.stderr)
    sys.exit(1)


def build_parser():
    p = Parser(
        prog=os.path.basename(sys.argv[0]),
        description=(
            "Replaces the first 256K (Modxo firmware region) of <original> with "
            "<new_modxo>, padded to 256K. The remaining data (PrometheOS and its "
            "bootloader) is left untouched."
        ),
    )
    p.add_argument("original", help="combined image (Modxo + PrometheOS)")
    p.add_argument("new_modxo", help="new Modxo firmware (must be <= 256K)")
    p.add_argument(
        "output",
        nargs="?",
        help="output path (default: <original>_new.bin next to the original)",
    )
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    orig_path, modxo_path = args.original, args.new_modxo

    if not os.path.isfile(orig_path):
        die(f"Original file not found: {orig_path}", parser)
    if not os.path.isfile(modxo_path):
        die(f"Modxo file not found: {modxo_path}", parser)

    if args.output:
        out_path = args.output
    else:
        base, _ = os.path.splitext(os.path.basename(orig_path))
        out_path = os.path.join(os.path.dirname(orig_path), f"{base}_new.bin")

    for src in (orig_path, modxo_path):
        if os.path.exists(out_path) and os.path.samefile(src, out_path):
            die("Output path must differ from the input files", parser)

    try:
        with open(orig_path, "rb") as f:
            orig = f.read()
        with open(modxo_path, "rb") as f:
            modxo = f.read()
    except OSError as e:
        die(f"Could not read input: {e}", parser)

    if len(orig) <= MODXO_SIZE:
        die(f"Original is {len(orig)} bytes; it must be larger than 256K", parser)
    if len(modxo) == 0:
        die("Modxo file is empty", parser)
    if len(modxo) > MODXO_SIZE:
        die(f"Modxo file is {len(modxo)} bytes; it must be <= {MODXO_SIZE} (256K)", parser)

    result = modxo + PAD_BYTE * (MODXO_SIZE - len(modxo)) + orig[MODXO_SIZE:]

    # Sanity checks before touching the disk
    assert len(result) == len(orig)
    assert result[MODXO_SIZE:] == orig[MODXO_SIZE:]

    try:
        with open(out_path, "wb") as f:
            f.write(result)
    except OSError as e:
        die(f"Failed to write {out_path}: {e}", parser)

    print(f"Wrote {out_path} ({len(result)} bytes)")


if __name__ == "__main__":
    main()
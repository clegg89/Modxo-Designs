#!/usr/bin/env python3
"""bin2uf2.py - convert a raw .bin to a UF2 file for RP2040 or RP2350"""

import argparse
import struct
import sys

FAMILIES = {
    "rp2040":        0xE48BFF56,
    "rp2350":        0xE48BFF59,  # RP2350 ARM Secure
    "rp2350-arm-ns": 0xE48BFF5B,  # RP2350 ARM Non-secure
    "rp2350-riscv":  0xE48BFF5A,  # RP2350 RISC-V
}

MAGIC0, MAGIC1, MAGIC_END = 0x0A324655, 0x9E5D5157, 0x0AB16F30
FLAG_FAMILY_ID = 0x00002000
CHUNK = 256


def main():
    p = argparse.ArgumentParser(description="Convert a raw .bin to UF2 for RP2040/RP2350.")
    p.add_argument("input", help="input .bin file")
    p.add_argument("output", help="output .uf2 file")
    p.add_argument("-c", "--chip", choices=FAMILIES, default="rp2040",
                   help="target chip (default: rp2040)")
    p.add_argument("-b", "--base", type=lambda x: int(x, 0), default=0x10000000,
                   help="base address (default: 0x10000000)")
    args = p.parse_args()

    family = FAMILIES[args.chip]

    with open(args.input, "rb") as f:
        data = f.read()

    if not data:
        sys.exit("Error: input file is empty")

    blocks = (len(data) + CHUNK - 1) // CHUNK

    with open(args.output, "wb") as f:
        for i in range(blocks):
            payload = data[i * CHUNK:(i + 1) * CHUNK].ljust(476, b"\x00")
            hdr = struct.pack("<8I", MAGIC0, MAGIC1, FLAG_FAMILY_ID,
                              args.base + i * CHUNK, CHUNK, i, blocks, family)
            f.write(hdr + payload + struct.pack("<I", MAGIC_END))

    print(f"Wrote {args.output}: {blocks} blocks, {args.chip} "
          f"(family 0x{family:08X}), base 0x{args.base:08X}")


if __name__ == "__main__":
    main()
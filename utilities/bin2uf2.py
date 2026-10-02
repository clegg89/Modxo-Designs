#!/usr/bin/env python3
# Convert modxo bin to uf2
# If you have picotools installed can also use:
#   picotool uf2 convert in.bin out.uf2 --offset 0x10000000 --family rp2040
import struct, sys

src, dst = sys.argv[1], sys.argv[2]
base   = 0x10000000
family = 0xE48BFF56   # RP2040
chunk  = 256

data = open(src, "rb").read()
n = (len(data) + chunk - 1) // chunk

with open(dst, "wb") as f:
    for i in range(n):
        payload = data[i * chunk:(i + 1) * chunk].ljust(476, b"\x00")
        hdr = struct.pack("<8I", 0x0A324655, 0x9E5D5157, 0x2000,
                          base + i * chunk, chunk, i, n, family)
        f.write(hdr + payload + struct.pack("<I", 0x0AB16F30))

print(f"Wrote {dst}: {n} blocks")
#!/usr/bin/env bash
# replace_modxo.sh - replace the Modxo firmware region in a combined PrometheOS image

set -euo pipefail

MODXO_SIZE=$((256 * 1024))   # 0x40000, size of the Modxo region

usage() {
    cat >&2 <<EOF
Usage: $(basename "$0") [-h] <original.bin> <new_modxo.bin> [output.bin]

Replaces the first 256K (Modxo firmware region) of <original.bin> with
<new_modxo.bin>, zero-padded to 256K. The remaining data (PrometheOS and
its bootloader) is left untouched.

Arguments:
  original.bin   Combined image (Modxo + PrometheOS)
  new_modxo.bin  New Modxo firmware (must be <= 256K)
  output.bin     Optional output path (default: <original>_new.bin)

Options:
  -h             Show this help
EOF
}

die() {
    echo "Error: $1" >&2
    echo >&2
    usage
    exit 1
}

# Option parsing
while getopts ":h" opt; do
    case $opt in
        h) usage; exit 0 ;;
        \?) die "Unknown option: -$OPTARG" ;;
    esac
done
shift $((OPTIND - 1))

if [ $# -lt 2 ] || [ $# -gt 3 ]; then
    die "Expected 2 or 3 arguments, got $#"
fi

orig="$1"
modxo="$2"

[ -f "$orig" ]  || die "Original file not found: $orig"
[ -f "$modxo" ] || die "Modxo file not found: $modxo"

if [ $# -eq 3 ]; then
    out="$3"
else
    base="${orig##*/}"
    dir="$(dirname "$orig")"
    out="$dir/${base%.*}_new.bin"
fi

orig_size=$(stat -c %s "$orig")
modxo_size=$(stat -c %s "$modxo")

[ "$orig_size" -gt "$MODXO_SIZE" ] || die "Original is $orig_size bytes; it must be larger than 256K"
[ "$modxo_size" -gt 0 ]            || die "Modxo file is empty"
[ "$modxo_size" -le "$MODXO_SIZE" ] || die "Modxo file is $modxo_size bytes; it must be <= $MODXO_SIZE (256K)"
[ "$orig" != "$out" ] && [ "$modxo" != "$out" ] || die "Output path must differ from the input files"

# Build the output: new Modxo (zero-padded to 256K) + everything after the old Modxo region
{
    cat "$modxo"
    head -c $((MODXO_SIZE - modxo_size)) /dev/zero
    tail -c +$((MODXO_SIZE + 1)) "$orig"
} > "$out" || die "Failed to write $out"

out_size=$(stat -c %s "$out")
if [ "$out_size" -ne "$orig_size" ]; then
    rm -f "$out"
    die "Output size ($out_size) does not match original size ($orig_size)"
fi

echo "Wrote $out ($out_size bytes)"
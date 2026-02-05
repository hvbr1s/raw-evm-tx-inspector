#!/usr/bin/env python3
import sys


def decode_rlp(data: bytes, pos: int = 0):
    b = data[pos]
    if b < 0x80:
        return bytes([b]), pos + 1
    elif b <= 0xB7:
        length = b - 0x80
        return data[pos + 1 : pos + 1 + length], pos + 1 + length
    elif b <= 0xBF:
        len_of_len = b - 0xB7
        length = int.from_bytes(data[pos + 1 : pos + 1 + len_of_len], "big")
        start = pos + 1 + len_of_len
        return data[start : start + length], start + length
    elif b <= 0xF7:
        length = b - 0xC0
        return _decode_list(data, pos + 1, pos + 1 + length), pos + 1 + length
    else:
        len_of_len = b - 0xF7
        length = int.from_bytes(data[pos + 1 : pos + 1 + len_of_len], "big")
        start = pos + 1 + len_of_len
        return _decode_list(data, start, start + length), start + length


def _decode_list(data: bytes, start: int, end: int) -> list:
    items = []
    pos = start
    while pos < end:
        item, pos = decode_rlp(data, pos)
        items.append(item)
    return items


def to_int(b: bytes) -> int:
    return int.from_bytes(b, "big") if b else 0


def wei_to_gwei(wei: int) -> float:
    return wei / 1e9


def wei_to_eth(wei: int) -> float:
    return wei / 1e18


def decode_type2_tx(raw_hex: str) -> dict:
    h = raw_hex.strip()
    if h.startswith(("0x", "0X")):
        h = h[2:]

    raw = bytes.fromhex(h)

    if raw[0] != 0x02:
        raise ValueError(f"Not a Type 2 tx (got prefix 0x{raw[0]:02x})")

    try:
        fields, _ = decode_rlp(raw, 1)
    except (IndexError, KeyError):
        fields, _ = decode_rlp(raw + b"\x00", 1)

    return {
        "chainId":              to_int(fields[0]),
        "nonce":                to_int(fields[1]),
        "maxPriorityFeePerGas": to_int(fields[2]),
        "maxFeePerGas":         to_int(fields[3]),
        "gasLimit":             to_int(fields[4]),
        "to":                   "0x" + fields[5].hex() if fields[5] else None,
        "value":                to_int(fields[6]),
        "data":                 "0x" + fields[7].hex() if fields[7] else "0x",
        "accessList":           fields[8] if len(fields) > 8 else [],
        "v":                    to_int(fields[9]) if len(fields) > 9 else 0,
        "r":                    "0x" + fields[10].hex() if len(fields) > 10 else "0x",
        "s":                    "0x" + fields[11].hex() if len(fields) > 11 else "0x",
    }


def format_tx(tx: dict) -> str:
    prio = tx["maxPriorityFeePerGas"]
    fee  = tx["maxFeePerGas"]
    glim = tx["gasLimit"]
    data = tx["data"]

    lines = [
        "=" * 60,
        "  EIP-1559 (Type 2) Transaction",
        "=" * 60,
        f"  Chain ID:             {tx['chainId']}",
        f"  Nonce:                {tx['nonce']}",
        "",
        "  --- Gas ---",
        f"  Max Priority Fee:     {prio:>20,} wei  ({wei_to_gwei(prio):.4f} Gwei)",
        f"  Max Fee Per Gas:      {fee:>20,} wei  ({wei_to_gwei(fee):.4f} Gwei)",
        f"  Gas Limit:            {glim:>20,}",
        f"  Max Tx Cost:          {wei_to_eth(glim * fee):.6f} ETH",
        "",
        "  --- Tx ---",
        f"  To:                   {tx['to']}",
        f"  Value:                {tx['value']} wei ({wei_to_eth(tx['value']):.6f} ETH)",
    ]
    if len(data) > 10:
        lines.append(f"  Function selector:    {data[:10]}")
        lines.append(f"  Calldata:             {(len(data) - 2) // 2} bytes")
        lines.append(f"  Calldata hex:         {data}")
    else:
        lines.append(f"  Data:                 {data}")
    lines.extend([
        "",
        "  --- Signature ---",
        f"  v: {tx['v']}  r: {tx['r'][:18]}...  s: {tx['s'][:18]}...",
        "=" * 60,
    ])
    return "\n".join(lines)


def print_tx(tx: dict):
    print(format_tx(tx))


def write_tx_to_file(tx: dict, filepath: str):
    with open(filepath, "w") as f:
        f.write(format_tx(tx) + "\n")
    print(f"Output written to {filepath}")


if __name__ == "__main__":
    output_file = None
    raw_tx = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] in ("-o", "--output") and i + 1 < len(args):
            output_file = args[i + 1]
            i += 2
        elif not raw_tx:
            raw_tx = args[i]
            i += 1
        else:
            i += 1

    if not raw_tx:
        raw_tx = input("Paste raw tx hex: ").strip()

    tx = decode_type2_tx(raw_tx)
    print_tx(tx)

    if output_file:
        write_tx_to_file(tx, output_file)
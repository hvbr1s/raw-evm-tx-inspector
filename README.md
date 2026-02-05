# decode-raw-evm-tx

Decode EIP-1559 (Type 2) raw Ethereum transactions. Zero external dependencies.

## Usage

```bash
# Decode and print to console
uv run decode.py <raw_tx_hex>

# Decode and save to file
uv run decode.py <raw_tx_hex> -o output.txt

# Interactive mode (prompts for input)
uv run decode.py
```

## Output

Displays chain ID, nonce, gas parameters, recipient, value, calldata info, and signature.

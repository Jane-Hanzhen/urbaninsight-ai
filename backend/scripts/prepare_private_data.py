from __future__ import annotations

import base64
import binascii
import os
import tempfile
from pathlib import Path


def decode_private_data(encoded_data: str, destination: Path) -> Path:
    compact_data = "".join(encoded_data.split())
    if not compact_data:
        raise ValueError("URBANINSIGHT_DATA_BASE64 is empty")

    try:
        decoded_data = base64.b64decode(compact_data, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("URBANINSIGHT_DATA_BASE64 is not valid Base64") from error

    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            delete=False,
        ) as temporary_file:
            temporary_file.write(decoded_data)
            temporary_path = Path(temporary_file.name)
        temporary_path.replace(destination)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    return destination


def main() -> None:
    encoded_data = os.getenv("URBANINSIGHT_DATA_BASE64", "")
    configured_path = os.getenv("URBANINSIGHT_DATA_PATH", "")
    if not configured_path:
        raise SystemExit("Error: URBANINSIGHT_DATA_PATH is not set.")

    try:
        destination = decode_private_data(encoded_data, Path(configured_path))
    except ValueError as error:
        raise SystemExit(f"Error: {error}") from error

    print(f"Decoded private dataset to {destination}")


if __name__ == "__main__":
    main()

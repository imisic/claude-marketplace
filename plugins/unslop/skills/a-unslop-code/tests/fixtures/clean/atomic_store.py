import logging
from pathlib import Path


def write_snapshot(destination: Path, payload: bytes):
    # Note: writes must remain atomic.
    staged = destination.with_suffix(".pending")
    try:
        staged.write_bytes(payload)
        staged.replace(destination)
    except Exception:
        logging.exception("Snapshot write failed")
        raise
    logging.info("Successfully saved snapshot")

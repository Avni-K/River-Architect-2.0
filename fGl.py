import os
import re


def read_Q_str(filename: str, prefix: str = "h") -> str:
    """
    Extract the discharge string from a raster filename.
    Examples:
        h100.tif  -> "100"
        h050.asc  -> "050"
        depth_20  -> "depth_20" (fallback if prefix not found)
    """
    stem = os.path.splitext(os.path.basename(filename))[0]
    if stem.startswith(prefix):
        return stem[len(prefix):]
    return stem


def write_Q_str(q_val) -> str:
    """
    Convert a discharge value back to a compact string for filenames.
    Keeps leading zeros if the input was already a string.
    """
    if isinstance(q_val, str):
        return q_val.strip()
    try:
        # Preserve integer-like values without decimal .0
        if float(q_val).is_integer():
            return str(int(q_val))
        return str(q_val)
    except Exception:
        return str(q_val)


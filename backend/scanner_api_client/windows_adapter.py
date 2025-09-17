import io
import os
import re
import tempfile
from typing import List, Union
from contextlib import redirect_stdout, redirect_stderr
from impacket.examples.secretsdump import LocalOperations, SAMHashes

# Thanks, chatGPT

_PWDUMP_LINE = re.compile(
    # Very forgiving matcher for: username:RID:LMHASH:NTHASH:::
    r"^[^:\r\n]+:[0-9]+:[0-9A-Fa-f*]{1,64}:[0-9A-Fa-f*]{1,64}:::$"
)

def _to_bytes(blob: Union[bytes, str]) -> bytes:
    if isinstance(blob, bytes):
        return blob
    # Hives are binary; latin-1 preserves raw bytes 0..255 (1:1 mapping).
    return blob.encode("latin-1", errors="ignore")

def _mktemp_write(prefix: str, suffix: str, data: bytes) -> str:
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return path

def extract_sam_hashes(sam_blob: Union[bytes, str], system_blob: Union[bytes, str]) -> List:
    """
    Extract local account password hashes from in-memory SAM + SYSTEM hive contents.

    Args:
        sam_blob: SAM hive data as bytes (preferred) or str (encoded latin-1).
        system_blob: SYSTEM hive data as bytes (preferred) or str (encoded latin-1).

    Returns:
        List[List[]]: [[username1, ntlm_of_username1], [username2, ntlm_of_username2] ...]
    """
    sam_bytes = _to_bytes(sam_blob)
    system_bytes = _to_bytes(system_blob)

    sam_path = system_path = None
    sam_hashes = None

    try:
        # Write temp hive files in BINARY mode
        sam_path = _mktemp_write("sam_", ".hive", sam_bytes)
        system_path = _mktemp_write("system_", ".hive", system_bytes)

        # Derive bootkey and prepare hasher
        local_ops = LocalOperations(system_path)
        bootkey = local_ops.getBootKey()

        sam_hashes = SAMHashes(sam_path, bootkey, isRemote=False)

        # Capture stdout/stderr that `dump()` prints (which includes the pwdump lines)
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            sam_hashes.dump()

        output = buf.getvalue()
        # Keep only pwdump-looking lines; ignore banners and info lines
        lines = [
            ln.strip()
            for ln in output.splitlines()
            if ln.strip()
        ]

        # Prefer strict pwdump lines; if none match, fall back to any colon-y lines
        pwdump_lines = [ln for ln in lines if _PWDUMP_LINE.match(ln)]
        if not pwdump_lines:
            # fallback heuristic: at least 6 colons often indicates pwdump-style
            pwdump_lines = [ln for ln in lines if ln.count(":") >= 6]

        result = []
        for ln in pwdump_lines:
            parts = ln.split(":")
            if len(parts) >= 4:
                username = parts[0]
                nt_hash = parts[3]
                result.append([username, nt_hash])

        return result

    except Exception as e:
        raise RuntimeError(f"Failed to extract SAM hashes: {e}") from e
    finally:
        # Ensure SAMHashes cleans up its resources
        try:
            if sam_hashes:
                sam_hashes.finish()
        except Exception:
            pass
        # Cleanup temp files
        for p in (sam_path, system_path):
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
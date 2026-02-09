import asyncio
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

MAIGRET_ROOT = Path(__file__).resolve().parent.parent / "maigret"
MAIGRET_DB_FILE = None
MAIGRET_AVAILABLE = False
maigret = None
MaigretDatabase = None

try:
    import maigret as _m
    from maigret.sites import MaigretDatabase as _MD
    maigret, MaigretDatabase, MAIGRET_AVAILABLE = _m, _MD, True
except Exception:
    if MAIGRET_ROOT.exists():
        sys.path.insert(0, str(MAIGRET_ROOT))
        try:
            import maigret as _m
            from maigret.sites import MaigretDatabase as _MD
            maigret, MaigretDatabase, MAIGRET_AVAILABLE = _m, _MD, True
        except Exception as e:
            logger.warning("Maigret unavailable: %s", e)

if MAIGRET_AVAILABLE and maigret:
    MAIGRET_DB_FILE = Path(maigret.__file__).resolve().parent / "resources" / "data.json"
    if not MAIGRET_DB_FILE.exists() and MAIGRET_ROOT.exists():
        fb = MAIGRET_ROOT / "maigret" / "resources" / "data.json"
        if fb.exists():
            MAIGRET_DB_FILE = fb


def _run_coro(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()
    return asyncio.run(coro)


def search(username, top_sites=500, timeout=5, max_connections=50, retries=0,
           id_type="username", tags=None, site_list=None, include_disabled=False,
           check_domains=False, cookies_file=None):
    if not MAIGRET_AVAILABLE:
        raise RuntimeError("Maigret is not available")
    if not MAIGRET_DB_FILE or not MAIGRET_DB_FILE.exists():
        raise FileNotFoundError("Maigret data file not found")

    db = MaigretDatabase().load_from_path(str(MAIGRET_DB_FILE))
    sites = db.ranked_sites_dict(top=top_sites, tags=tags, names=site_list,
                                  disabled=include_disabled, id_type=id_type)

    sl = logging.getLogger("maigret")
    sl.setLevel(logging.WARNING)

    results = _run_coro(maigret.search(
        username=username, site_dict=sites, timeout=timeout, logger=sl,
        id_type=id_type, max_connections=max_connections, no_progressbar=True,
        retries=retries, check_domains=check_domains,
        cookies=str(cookies_file) if cookies_file else None,
    ))
    return results, len(sites)

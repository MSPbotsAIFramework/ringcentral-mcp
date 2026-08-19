from .._json import error_envelope

NO_TOKEN = error_envelope(
    "not_configured",
    "No RingCentral credentials. Send the X-RingCentral-Client-Id, "
    "X-RingCentral-Client-Secret, and X-RingCentral-Jwt headers.",
    False,
)

# SOP §2.5 fallback ceiling: default <=50, hard cap <=200. RingCentral's own
# documented per-page maximums (call-log endpoints: 1000; directory/entries:
# 2000; other list endpoints: undocumented, vendor-side default 100 with no
# stated cap) are all looser than 200, so the SOP ceiling is the binding
# constraint everywhere in this service — there is no endpoint here where the
# vendor's real max is stricter than 200.
MAX_PER_PAGE = 200


def clamp_per_page(value: int | None) -> int | None:
    if value is None:
        return None
    return min(value, MAX_PER_PAGE)

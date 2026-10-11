"""Demo users. Region values are a whitelist; the guest token never takes a free-form clause."""

from __future__ import annotations

ALLOWED_REGIONS = ("north", "south", "east", "west")

USERS: dict[str, dict[str, str | None]] = {
    "sara": {"display_name": "سارا احمدی", "region": "north"},
    "reza": {"display_name": "رضا کریمی", "region": "south"},
    "niloofar": {"display_name": "نیلوفر مرادی", "region": "east"},
    "office": {"display_name": "دفتر مرکزی", "region": None},
}


def rls_rules(user_id: str) -> list[dict[str, str]]:
    """Security rules only. An unknown region is a bug, not a filter to forward."""
    user = USERS[user_id]
    region = user["region"]
    if region is None:
        return []
    if region not in ALLOWED_REGIONS:
        raise ValueError(f"region {region!r} is not in the whitelist")
    return [{"clause": f"region IN ('{region}')"}]

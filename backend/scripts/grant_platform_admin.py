"""Grant the platform_admin realm role to an existing Keycloak user.

    make admin-user EMAIL=you@example.com
    (or)  python -m scripts.grant_platform_admin you@example.com
"""
from __future__ import annotations

import asyncio
import sys

from app.services.keycloak_admin import KeycloakAdmin


async def main(email: str) -> None:
    user_id = await KeycloakAdmin().grant_role_by_email(email)
    print(f"Granted platform_admin to {email} ({user_id}). They must sign in again.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python -m scripts.grant_platform_admin <email>")
    asyncio.run(main(sys.argv[1]))

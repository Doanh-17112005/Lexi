"""Create a local super-admin without embedding credentials in source code.

Example (PowerShell):
    $env:LEXILINGO_BOOTSTRAP_ADMIN_PASSWORD = '<strong password>'
    python scripts/create_default_admin.py --email admin@example.com

The script refuses to run against a production configuration and never prints
the password. Existing passwords are preserved unless --reset-password is set.
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import TypeAdapter
from pydantic.networks import EmailStr
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.rbac import Role
from app.models.user import User
from app.schemas.auth import RegisterRequest


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or update a local super-admin")
    parser.add_argument("--email", required=True, help="Administrator email address")
    parser.add_argument("--username", help="Defaults to the email local part")
    parser.add_argument("--display-name", default="Development Super Admin")
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="Replace the password if the user already exists",
    )
    return parser.parse_args()


def _read_password() -> str:
    password = os.getenv("LEXILINGO_BOOTSTRAP_ADMIN_PASSWORD")
    if not password:
        if not sys.stdin.isatty():
            raise RuntimeError(
                "Set LEXILINGO_BOOTSTRAP_ADMIN_PASSWORD for non-interactive use"
            )
        password = getpass.getpass("New admin password: ")

    # Reuse the same password policy as public registration without retaining
    # the secret in a settings object, log, or source-controlled file.
    RegisterRequest.validate_password_strength(password)
    return password


def _normalise_username(email: str, requested: str | None) -> str:
    candidate = requested or email.split("@", 1)[0]
    candidate = re.sub(r"[^a-zA-Z0-9._-]", "_", candidate).strip("._-")
    if len(candidate) < 3:
        candidate = f"admin_{candidate or 'local'}"
    return candidate[:50]


async def create_local_admin(args: argparse.Namespace) -> None:
    if settings.is_production:
        raise RuntimeError("This bootstrap script is disabled in production")

    email = str(TypeAdapter(EmailStr).validate_python(args.email)).lower()
    username = _normalise_username(email, args.username)
    password = _read_password()

    async with AsyncSessionLocal() as db:
        try:
            role_result = await db.execute(select(Role).where(Role.slug == "super_admin"))
            role = role_result.scalar_one_or_none()
            if role is None:
                role = Role(
                    id=uuid.uuid4(),
                    name="Super Administrator",
                    slug="super_admin",
                    description="Full system access",
                    level=100,
                )
                db.add(role)
                await db.flush()

            user_result = await db.execute(select(User).where(User.email == email))
            user = user_result.scalar_one_or_none()

            if user is None:
                username_result = await db.execute(
                    select(User.id).where(User.username == username)
                )
                if username_result.scalar_one_or_none() is not None:
                    raise RuntimeError(f"Username already exists: {username}")
                user = User(
                    id=uuid.uuid4(),
                    email=email,
                    username=username,
                    display_name=args.display_name,
                    hashed_password=get_password_hash(password),
                    is_active=True,
                    is_verified=True,
                    role_id=role.id,
                )
                db.add(user)
                action = "Created"
            else:
                if args.reset_password:
                    user.hashed_password = get_password_hash(password)
                user.is_active = True
                user.is_verified = True
                user.role_id = role.id
                action = "Updated"

            await db.commit()
        except Exception:
            await db.rollback()
            raise

    password_note = "password reset" if args.reset_password else "password preserved if existing"
    print(f"{action} local super-admin {email} ({password_note}).")


if __name__ == "__main__":
    asyncio.run(create_local_admin(_arguments()))

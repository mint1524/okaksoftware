from __future__ import annotations

import getpass

from app.core.security import hash_password


def main() -> None:
    password = getpass.getpass("Enter new admin password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        raise SystemExit("Passwords do not match")
    if not password:
        raise SystemExit("Password cannot be empty")
    hashed = hash_password(password)
    print("Add this value to OKAK_ADMIN_PASSWORD_HASH:")
    print(hashed)


if __name__ == "__main__":
    main()

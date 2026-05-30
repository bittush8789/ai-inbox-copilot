import os
from google.oauth2.credentials import Credentials

TOKEN_FILE = "token.json"

def load_stored_credentials() -> Credentials | None:
    if os.path.exists(TOKEN_FILE):
        try:
            return Credentials.from_authorized_user_file(TOKEN_FILE)
        except Exception:
            return None
    return None

def save_credentials(credentials: Credentials) -> None:
    try:
        with open(TOKEN_FILE, "w") as f:
            f.write(credentials.to_json())
    except Exception as e:
        raise IOError(f"Failed to write credentials token file: {e}")

def delete_stored_credentials() -> None:
    if os.path.exists(TOKEN_FILE):
        try:
            os.remove(TOKEN_FILE)
        except Exception as e:
            raise IOError(f"Failed to remove credentials token file: {e}")

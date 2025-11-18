from __future__ import annotations

import json
import os


CONFIG_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "configurations.json")
)


###############################################################################
def coerce_str_value(value: str | None) -> str | None:
    if value is None:
        return None
    candidate = value.strip()
    return candidate or None


# -------------------------------------------------------------------------
def coerce_int_value(value: str | None, minimum: int, maximum: int) -> int | None:
    candidate = coerce_str_value(value)
    if candidate is None:
        return None
    try:
        parsed = int(candidate)
    except ValueError:
        return None
    return max(minimum, min(maximum, parsed))


# -------------------------------------------------------------------------
def load_configuration() -> dict:
    if not os.path.exists(CONFIG_FILE):
        raise RuntimeError(f"Configuration file not found at {CONFIG_FILE}")
    with open(CONFIG_FILE, "r", encoding="utf-8") as handle:
        return json.load(handle)


# -------------------------------------------------------------------------
def persist_configuration(payload: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


# -------------------------------------------------------------------------
def apply_overrides() -> bool:
    overrides = {
        "selected_database": coerce_str_value(os.getenv("ADSORFIT_DB_ENGINE")),
        "host": coerce_str_value(os.getenv("ADSORFIT_DB_HOST")),
        "port": coerce_int_value(os.getenv("ADSORFIT_DB_PORT"), 1, 65535),
        "database_name": coerce_str_value(os.getenv("ADSORFIT_DB_NAME")),
        "username": coerce_str_value(os.getenv("ADSORFIT_DB_USER")),
        "password": coerce_str_value(os.getenv("ADSORFIT_DB_PASSWORD")),
        "insert_batch_size": coerce_int_value(
            os.getenv("ADSORFIT_DB_BATCH_SIZE"), 1, 1_000_000
        ),
    }
    if not any(value is not None for value in overrides.values()):
        return False

    configuration = load_configuration()
    database_section = configuration.setdefault("database", {})
    if overrides["selected_database"]:
        database_section["selected_database"] = overrides["selected_database"].lower()
    if overrides["host"] is not None:
        database_section["host"] = overrides["host"]
    if overrides["port"] is not None:
        database_section["port"] = overrides["port"]
    if overrides["database_name"] is not None:
        database_section["database_name"] = overrides["database_name"]
    if overrides["username"] is not None:
        database_section["username"] = overrides["username"]
    if overrides["password"] is not None:
        database_section["password"] = overrides["password"]
    if overrides["insert_batch_size"] is not None:
        database_section["insert_batch_size"] = overrides["insert_batch_size"]

    persist_configuration(configuration)
    return True


# -------------------------------------------------------------------------
def main() -> None:
    if apply_overrides():
        print("[INFO] Database configuration updated from environment overrides.")
    else:
        print("[INFO] No database overrides detected; configuration unchanged.")


if __name__ == "__main__":
    main()

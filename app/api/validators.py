import json
from typing import List, Optional

from fastapi import HTTPException, status

from talkingdb.clients.sqlite import sqlite_conn
from talkingdb.helpers.namespace import store as namespace_store

from app.core import config


def _unprocessable(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"error_code": "VALIDATION_ERROR", "message": message},
    )


def clean_optional_text(value: Optional[str]) -> Optional[str]:
    """Trim a free-text form field; treat blank as absent."""
    if value is None:
        return None
    value = value.strip()
    return value or None


def parse_suggested_queries(raw: Optional[str]) -> Optional[List[str]]:
    if raw is None or raw.strip() == "":
        return None

    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        raise _unprocessable("suggested_queries must be a JSON array of strings")

    if not isinstance(data, list):
        raise _unprocessable("suggested_queries must be a JSON array of strings")
    if len(data) > config.MAX_SUGGESTED_QUERIES:
        raise _unprocessable(
            f"at most {config.MAX_SUGGESTED_QUERIES} suggested_queries are allowed"
        )

    cleaned: List[str] = []
    for item in data:
        if not isinstance(item, str):
            raise _unprocessable("each suggested query must be a string")
        text = item.strip()
        if not text:
            raise _unprocessable("suggested queries must not be blank")
        cleaned.append(text)

    return cleaned or None


def validate_namespace(namespace: Optional[str]) -> Optional[str]:
    namespace = clean_optional_text(namespace)
    if namespace is None:
        return None
    with sqlite_conn() as conn:
        if namespace_store.get_namespace(conn, namespace) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "NAMESPACE_NOT_FOUND",
                    "message": f"Unknown namespace: {namespace}",
                },
            )
    return namespace

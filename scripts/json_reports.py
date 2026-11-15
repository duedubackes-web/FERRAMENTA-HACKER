"""Shared bounded JSON decoding for offline report adapters."""
import json


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def _invalid_number(value):
    raise ValueError(f'Invalid JSON number: {value}')


def decode_object(data: bytes, label: str, max_bytes: int) -> dict:
    if len(data) > max_bytes:
        raise ValueError(f'{label} exceeds the {max_bytes // (1024 * 1024)} MiB input limit')
    try:
        raw = json.loads(data.decode('utf-8-sig'), object_pairs_hook=_object, parse_constant=_invalid_number)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError(f'Invalid UTF-8 {label}: {error}') from error
    if not isinstance(raw, dict):
        raise ValueError(f'{label} must be a JSON object')
    return raw


def optional_text(record: dict, key: str, context: str):
    value = record.get(key)
    if value is not None and not isinstance(value, str):
        raise ValueError(f'{context}.{key} must be a string or null')
    return value

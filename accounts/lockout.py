"""5 wrong passwords -> locked for 5 minutes (per username + address)."""
import hashlib

from django.core.cache import cache

MAX_TRIES = 5
LOCK_SECONDS = 300


def _key(username, ip):
    return "loginfail:" + hashlib.sha256(f"{username}|{ip}".encode()).hexdigest()


def is_locked(username, ip):
    return cache.get(_key(username, ip), 0) >= MAX_TRIES


def record_failure(username, ip):
    cache.set(_key(username, ip), cache.get(_key(username, ip), 0) + 1, LOCK_SECONDS)


def clear(username, ip):
    cache.delete(_key(username, ip))

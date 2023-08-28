#!/usr/bin/python
import os

from dotenv import load_dotenv
from postgrest._async.client import AsyncPostgrestClient

load_dotenv()

def make_db_client():
    base_url = os.environ.get("BASE_URL")
    if not base_url:
        print("error: missing environment varibles.")
        exit(1)

    return AsyncPostgrestClient(base_url, schema="api", headers={
        'Authorization': f'Bearer {os.environ.get("TOKEN")}',
        "Accept": "application/json",
        "Content-Type": "application/json",
        })


def check_duplicate(response): 
    if hasattr(response, "code"):
        return any(response['code'] == 23505)
    return False

def check_error(response) -> bool: 
    failed = hasattr(response, "code")
    if failed: print(f"ERROR: {response}")
    return failed
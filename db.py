#!/bin/python
import os
from supabase.client import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not key or not url:
    print("error: missing environment varibles.")
    exit(1)

supabase = create_client(url, key)

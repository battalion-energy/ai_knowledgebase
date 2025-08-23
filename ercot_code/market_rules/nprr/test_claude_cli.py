#!/usr/bin/env python3
"""Test Claude CLI with a simple NPRR analysis"""

import subprocess
import json

# Simple test prompt
prompt = """Analyze this NPRR: "Improve battery storage integration in ERCOT market".

Provide a JSON response with these exact keys:
{
  "summary": "One sentence summary",
  "bess_impact": 5,
  "solar_impact": 2,
  "wind_impact": 1
}

Just the JSON, no other text."""

print("Testing Claude CLI...")
result = subprocess.run(
    ['claude', '-p', prompt],
    capture_output=True,
    text=True,
    timeout=30
)

print(f"Return code: {result.returncode}")
print(f"Output length: {len(result.stdout)} chars")
print("First 500 chars of output:")
print(result.stdout[:500])

if result.stderr:
    print(f"Errors: {result.stderr}")
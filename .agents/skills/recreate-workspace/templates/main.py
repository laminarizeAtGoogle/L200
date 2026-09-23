import os
import sys

print(f"Python version: {sys.version}")
print(f"Virtualenv prefix: {sys.prefix}")

import google.adk
import ipykernel
import pandas as pd

print("\nImported modules successfully:")
print(f" - google.adk version: {getattr(google.adk, '__version__', 'unknown')}")
print(f" - pandas version: {pd.__version__}")
print(f" - ipykernel version: {ipykernel.__version__}")

cloudsdk_config = os.environ.get("CLOUDSDK_CONFIG", "Not set")
gac = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "Not set")
print(f"\nEnvironment variables:")
print(f" - CLOUDSDK_CONFIG: {cloudsdk_config}")
print(f" - GOOGLE_APPLICATION_CREDENTIALS: {gac}")
print("\nEnvironment verification successful!")


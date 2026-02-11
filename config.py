import os

# Base directory of the project (folder containing this file)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Default location to store per-condition outputs (created if missing).
dir2conditions = os.path.join(BASE_DIR, "conditions")
os.makedirs(dir2conditions, exist_ok=True)

# Unit conversion constant: feet to meters.
ft2m = 0.3048


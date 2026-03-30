"""
Conftest: set test DB env var BEFORE importing app modules.
"""
import os
import sys
import warnings
warnings.filterwarnings("ignore")

# Must set before any app imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_crf.db"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

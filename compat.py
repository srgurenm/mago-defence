# Compatibility module - redirects old imports to new src module
# This allows gradual migration from old file structure to new organized structure

import sys
import os

# Add src to path if not already there
if 'src' not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Re-export everything from src modules for backwards compatibility
from src.constants import *
from src.player import *
from src.sprites import *

# Keep the old classes available for direct import
# (these are now re-exported from src modules)

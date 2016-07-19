"""Package for assembling ``foremast`` configuration files.

Retrieve the necessary configuration files from GitLab, merge with the default
templates, and output a master *settings* file to be consumed by other
``foremast`` modules.
"""
from .outputs import *
from .prepare_configs import *

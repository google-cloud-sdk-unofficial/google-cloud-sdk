"""__init__.py -- The git module of dulwich."""

# We use the following mechanism to allow users to build with the next version
# of dulwich without modifying the caller's import lines.
# Inspired by go/ipython-upgrade-mechanics

import logging

# pylint: disable=g-import-not-at-top

try:
  import dulwich.next
  logging.info('Using new version of dulwich')
except ImportError:
  import dulwich.stable
  logging.info('Using stable version of dulwich')

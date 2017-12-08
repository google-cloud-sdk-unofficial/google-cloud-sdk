# Copyright 2013 Google Inc. All Rights Reserved.

"""gcloud command line tool."""

import os
import sys

_THIRD_PARTY_DIR = os.path.join(os.path.dirname(__file__), 'third_party')

if os.path.isdir(_THIRD_PARTY_DIR):
  sys.path.insert(0, _THIRD_PARTY_DIR)


def main():
  # pylint:disable=g-import-not-at-top
  try:
    import googlecloudsdk.gcloud_main
  except ImportError as err:
    # We DON'T want to suggest `gcloud components reinstall` here, as we know
    # that no commands will work.
    sys.stderr.write(
        ('ERROR: gcloud failed to load: {0}\n\n'
         'This usually indicates corruption in your gcloud installation. '
         'Please reinstall the Cloud SDK using the instructions here:\n'
         '    https://cloud.google.com/sdk/\n').format(err))
    sys.exit(1)
  sys.exit(googlecloudsdk.gcloud_main.main())


if __name__ == '__main__':
  main()

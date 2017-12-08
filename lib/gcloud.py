# Copyright 2013 Google Inc. All Rights Reserved.

"""gcloud command line tool."""

import os
import sys

_THIRD_PARTY_DIR = os.path.join(os.path.dirname(__file__), 'third_party')

if os.path.isdir(_THIRD_PARTY_DIR):
  sys.path.insert(0, _THIRD_PARTY_DIR)


def main():
  # pylint:disable=g-import-not-at-top
  import googlecloudsdk.gcloud_main
  sys.exit(googlecloudsdk.gcloud_main.main())


if __name__ == '__main__':
  main()

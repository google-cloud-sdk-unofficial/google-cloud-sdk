# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This package flattens image metadata into a single tarball."""



import argparse
import logging
import tarfile

from containerregistry.client.v2_2 import docker_image as v2_2_image
from containerregistry.tools import logging_setup

parser = argparse.ArgumentParser(description='Flatten container images.')

# The name of this flag was chosen for compatibility with docker_pusher.py
parser.add_argument('--tarball', action='store',
                    help='The image path in "docker save" tarball format.')

# Output arguments.
parser.add_argument('--filesystem', action='store',
                    help='The name of where to write the filesystem tarball.')

parser.add_argument('--metadata', action='store',
                    help=('The name of where to write the container '
                          'startup metadata.'))


def main():
  logging_setup.DefineCommandLineArgs(parser)
  args = parser.parse_args()
  logging_setup.Init(args=args)

  if not args.filesystem or not args.metadata or not args.tarball:
    raise Exception(
        '--filesystem, --tarball and --metadata are required flags.')

  logging.info('Loading v2.2 image from tarball ...')
  with v2_2_image.FromTarball(args.tarball) as v2_2_img:
    with tarfile.open(args.filesystem, 'w') as tar:
      v2_2_image.extract(v2_2_img, tar)

    with open(args.metadata, 'w') as f:
      f.write(v2_2_img.config_file())

if __name__ == '__main__':
  main()

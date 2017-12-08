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
"""Import image command."""

from googlecloudsdk.api_lib.compute import daisy_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.images import flags
from googlecloudsdk.core import log

_WORKFLOW = '../workflows/image_import/import_image.wf.json'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Import(base.CreateCommand):
  """Import a Google Compute Engine image."""

  @staticmethod
  def Args(parser):
    Import.DISK_IMAGE_ARG = flags.MakeDiskImageArg()
    Import.DISK_IMAGE_ARG.AddArgument(parser, operation_type='create')

    parser.add_argument(
        '--source-uri',
        required=True,
        help=('The Google Cloud Storage URI of the '
              'virtual disk file to import.'),
    )
    daisy_utils.AddCommonDaisyArgs(parser)

  def Run(self, args):
    variables = """source_disk_file={0},disk_size=50g,image_name={1}""".format(
        args.source_uri, args.image_name)

    log.warn('Importing image, this may take up to 1 hour.')
    return daisy_utils.RunDaisyBuild(args, _WORKFLOW, variables)

Import.detailed_help = {
    'brief': 'Import a Google Compute Engine image',
    'DESCRIPTION': """\
        *{command}* imports Virtual Disk images, such as VMWare VMDK files
        and VHD files, into Google Compute Engine.

        To import an image into Google Compute Engine upload the Virtual Disk
        image to Google Cloud storage before running this command.

        Importing images involves 3 steps:
        *  Upload the virtual disk file to Google Cloud Storage.
        *  Import the image to Google Compute Engine (this command).
        *  Translate the image to make a bootable image.
        """,
}

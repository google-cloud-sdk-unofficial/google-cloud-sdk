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
"""Translate image command."""

from googlecloudsdk.api_lib.compute import daisy_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.images import flags

_OS_CHOICES = {'debian-8': 'debian/translate_debian_8.wf.json',
               'debian-9': 'debian/translate_debian_9.wf.json',
               'centos-6': 'enterprise_linux/translate_centos_6.wf.json',
               'centos-7': 'enterprise_linux/translate_centos_7.wf.json',
               'rhel-6': 'enterprise_linux/translate_rhel_6_licensed.wf.json',
               'rhel-7': 'enterprise_linux/translate_centos_7_licensed.wf.json',
               'rhel-6-byol': 'enterprise_linux/translate_rhel_6_byol.wf.json',
               'rhel-7-byol': 'enterprise_linux/translate_rhel_7_byol.wf.json',
               'ubuntu-1404': 'ubuntu/translate_ubuntu_1404.wf.json',
               'ubuntu-1604': 'ubuntu/translate_ubuntu_1604.wf.json',
               'windows-2008r2': 'windows/translate_windows_2008_r2.wf.json',
               'windows-2012r2': 'windows/translate_windows_2012_r2.wf.json',
               'windows-2016': 'windows/translate_windows_2016.wf.json',
              }
_WORKFLOWS_URL = ('https://github.com/GoogleCloudPlatform/compute-image-tools/'
                  'tree/master/daisy_workflows/image_import')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Translate(base.CreateCommand):
  """Translate an imported image to make a bootable image."""

  @staticmethod
  def Args(parser):
    flags.DESTINATION_IMAGE_ARG.AddArgument(parser, operation_type='create')
    flags.SOURCE_IMAGE_ARG.AddArgument(parser, operation_type='translate')

    workflow = parser.add_mutually_exclusive_group(required=True)

    workflow.add_argument(
        '--os',
        choices=sorted(_OS_CHOICES.keys()),
        help='Specifies the OS of the image being translated.'
    )
    workflow.add_argument(
        '--custom-workflow',
        help=("""\
              Specifies a custom workflow to use for the image translate.
              Workflow should be relative to the image_import directory here:
              []({0}). For example: ``debian/translate_debian_8.wf.json''"""
              .format(_WORKFLOWS_URL)),
    )
    daisy_utils.AddCommonDaisyArgs(parser)

  def Run(self, args):
    if args.os:
      workflow = _OS_CHOICES[args.os]
    else:
      workflow = args.custom_workflow
    workflow_path = '../workflows/image_import/{0}'.format(workflow)
    variables = """source_image=global/images/{0},image_name={1}""".format(
        args.source_image, args.destination_image)
    return daisy_utils.RunDaisyBuild(args, workflow_path, variables)

Translate.detailed_help = {
    'brief': 'Translate an imported image to make a bootable image',
    'DESCRIPTION': """\
        *{command}* converts an imported image to one that is
        bootable on Google Compute Engine. It uses the `--os` flag
        to choose the appropriate translation.

        Importing images involves 3 steps:
        *  Upload the virtual disk file to Google Cloud Storage.
        *  Import the image to Google Compute Engine.
        *  Translate the image to make a bootable image (this command).
        """,
}

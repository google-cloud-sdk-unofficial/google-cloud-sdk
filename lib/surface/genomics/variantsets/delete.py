# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Implementation of gcloud genomics variantsets delete.
"""

from googlecloudsdk.api_lib import genomics as lib
from googlecloudsdk.api_lib.genomics import genomics_util
from googlecloudsdk.api_lib.genomics.exceptions import GenomicsError
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.Command):
  """Deletes a variant set.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('variant_set_id',
                        type=int,
                        help='The ID of the variant set to be deleted.')

  @genomics_util.ReraiseHttpException
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace, All the arguments that were provided to this
        command invocation.

    Raises:
      HttpException: An http error response was received while executing api
          request.
      GenomicsError: if canceled by the user.
    Returns:
      None
    """

    prompt_message = (
        'Deleting variant set {0} will also delete all its contents '
        '(variants, callsets, and calls).'
        ).format(args.variant_set_id)

    if not console_io.PromptContinue(message=prompt_message):
      raise GenomicsError('Deletion aborted by user.')

    apitools_client = self.context[lib.GENOMICS_APITOOLS_CLIENT_KEY]
    genomics_messages = self.context[lib.GENOMICS_MESSAGES_MODULE_KEY]

    req = genomics_messages.GenomicsVariantsetsDeleteRequest(
        variantSetId=str(args.variant_set_id),
    )

    ret = apitools_client.variantsets.Delete(req)
    log.DeletedResource('{0}'.format(args.variant_set_id))
    return ret

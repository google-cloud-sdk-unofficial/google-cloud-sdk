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
"""Command to Classify Text into Catergories."""

from googlecloudsdk.api_lib.ml.language import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml.language import flags
from googlecloudsdk.command_lib.ml.language import language_command_util


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ClassifyText(base.Command):
  """Classifies input document into categories.

  Classifies input document into categories. Returns a list of categories
  representing the document. Only the most relevant categories a document are
  returned e.g. if  `/Science` and `/Science/Astronomy` both apply to a
  document, then only the `/Science/Astronomy` category is returned, as it is
  the more specific result.


  {service_account_help}

  {language_help}
  """
  detailed_help = {
      'service_account_help': language_command_util.SERVICE_ACCOUNT_HELP,
      'language_help': language_command_util.LANGUAGE_HELP_ENTITY_SENTIMENT
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('json')
    flags.AddLanguageFlags(parser, with_encoding=False)

  def Run(self, args):
    feature = 'classifyText'
    return language_command_util.RunLanguageCommand(
        feature,
        content_file=args.content_file,
        content=args.content,
        language=args.language,
        content_type=args.content_type,
        api_version=util.LANGUAGE_BETA_VERSION
    )

# -*- coding: utf-8 -*- #
# Copyright 2024 Google Inc. All Rights Reserved.
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
"""`gcloud dataproc-gdc instances create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import uuid

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc_gdc.spark_applications import basecreate as baseSparkApplication
from googlecloudsdk.command_lib.util.args import labels_util

DATAPROCGDC_API_NAME = 'dataprocgdc'
DATAPROCGDC_API_VERSION = 'v1alpha1'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class SparkSql(baseSparkApplication.BaseGDCSparkApplicationCommand):
  """Create a Dataproc GDC Spark SQL application.

  A Spark SQL application that run locally on the Dataproc
  GDC cluster.
  """

  detailed_help = {'EXAMPLES': """\
          To create a Dataproc GDC spark sql application  with name
          `my-application` in location `us-central1` running on a service
          instance `my-instance`, run:

          $ {command} my-application --instance=my-instance
          --location=us-central1 --project=test-project

          """}

  @staticmethod
  def Args(parser):
    baseSparkApplication.BaseGDCSparkApplicationCommand.Args(parser)
    parser.add_argument(
        '--file',
        help='The HCFS URI of the script that contains SQL queries',
    )
    parser.add_argument(
        '--params',
        type=arg_parsers.ArgDict(),
        metavar='PROPERTY=VALUE',
        help=(
            'Mapping of query variable names to values (equivalent to the '
            'Spark SQL command: SET `name="value";`) '
        ),
    )
    parser.add_argument(
        '--query-file',
        help='The HCFS URI of the script that contains SQL queries.',
    )
    parser.add_argument(
        '--jars',
        type=arg_parsers.ArgList(),
        metavar='JAR',
        default=[],
        help=(
            'Comma separated list of jar files to be provided to the '
            'executor and driver classpaths.'
        ),
    )

  def Run(self, args):
    messages = apis.GetMessagesModule('dataprocgdc', 'v1alpha1')
    application_ref = args.CONCEPTS.application.Parse()
    application_environment_ref = args.CONCEPTS.application_environment.Parse()

    if args.annotations:
      annotations = encoding.DictToAdditionalPropertyMessage(
          args.annotations,
          messages.SparkApplication.AnnotationsValue,
          sort_items=True,
      )
    else:
      annotations = None

    request_id = args.request_id or uuid.uuid4().hex
    application_environment = None
    if application_environment_ref:
      application_environment = application_environment_ref.RelativeName()

    create_req = messages.DataprocgdcProjectsLocationsServiceInstancesSparkApplicationsCreateRequest(
        parent=application_ref.Parent().RelativeName(),
        requestId=request_id,
        sparkApplicationId=application_ref.Name(),
        sparkApplication=messages.SparkApplication(
            applicationEnvironment=application_environment,
            displayName=args.display_name,
            labels=labels_util.ParseCreateArgs(
                args, messages.SparkApplication.LabelsValue
            ),
            annotations=annotations,
            name=application_ref.RelativeName(),
            namespace=args.namespace,
            properties=args.properties,
            version=args.version,
            sparkSqlApplicationConfig=messages.SparkSqlApplicationConfig(
                jarFileUris=args.jars or [],
                queryFileUri=args.file,
                scriptVariables=args.params,
            ),
        ),
    )
    super().Submit(args, application_ref, create_req)

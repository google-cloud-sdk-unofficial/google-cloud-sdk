# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Create command for Backup for GKE restore."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.backup_restore import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.backup_restore import resource_args
from googlecloudsdk.command_lib.container.backup_restore import util as command_util
from googlecloudsdk.command_lib.util.args import labels_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Creates a restore.

  Creates a Backup for GKE restore.

  ## EXAMPLES

  To create a restore ``my-restore'' in location ``us-central1'', run:

    $ {command} my-restore --project=my-project --location=us-central1

  """

  @staticmethod
  def Args(parser):
    resource_args.AddRestoreArg(parser)
    group = parser.add_group(mutex=True)
    group.add_argument(
        '--async',
        required=False,
        action='store_true',
        default=False,
        help='Return immediately, without waiting for the operation in progress to complete.'
    )
    group.add_argument(
        '--wait-for-completion',
        required=False,
        action='store_true',
        default=False,
        help='Wait for the created restore to complete.')
    parser.add_argument(
        '--backup',
        type=str,
        required=True,
        help="""
        Relative name of the backup from which to restore. Value must be entered
        as a relative name, e.g.
        `projects/<project>/locations/<location>/backupPlans/<backupPlans>/backups/<backup>`.
        """)
    parser.add_argument(
        '--cluster',
        type=str,
        required=True,
        help="""
        Relative name of the target cluster in which the restore will occur.
        Value must be entered as a relative name, e.g.
        `projects/<project>/locations/<location>/clusters/<cluster>` for a regional cluster
        or
        `projects/<project>/zones/<zone>/clusters/<cluster>` for a zonal cluster.
        """)
    parser.add_argument(
        '--volume-data-restore-policy',
        type=str,
        choices=[
            'RESTORE_VOLUME_DATA_FROM_BACKUP',
            'REUSE_VOLUME_HANDLE_FROM_BACKUP', 'NO_VOLUME_DATA_RESTORATION'
        ],
        default='NO_VOLUME_DATA_RESTORATION',
        help='Define how data is populated for restored volumes.')
    parser.add_argument(
        '--cluster-resource-conflict-policy',
        type=str,
        choices=['USE_EXISTING_VERSION', 'USE_BACKUP_VERSION'],
        required=True,
        help="""
        Define how to handle restore-time conflicts for cluster-scoped
        resources.
        """)
    parser.add_argument(
        '--namespaced-resource-restore-mode',
        type=str,
        choices=['DELETE_AND_RESTORE', 'FAIL_ON_CONFLICT'],
        required=True,
        help="""
        Define how to handle restore-time conflicts for namespaced resources.
        """)
    parser.add_argument(
        '--cluster-resource-restore-scope',
        type=str,
        help="""
        List of cluster-scoped resource types to be restored. Not specifying
        this means NO cluster resource will be restored. The format of a
        resource is "<group>/<kind>", e.g.
        `storage.k8s.io/StorageClass` for StorageClass.
        """)
    namespaced_resource_restore_group = parser.add_group(
        mutex=True,
        required=True,
        help="""
        Namespaced resource restore scope specifies selected namespaces
        resources to restore.
        """)
    base.Argument(
        '--all-namespaces',
        action='store_true',
        help='If true, restore all namespaced resources in the backup.'
    ).AddToParser(namespaced_resource_restore_group)
    base.Argument(
        '--selected-namespaces',
        type=str,
        help="""
        List of selected namespaces to restore. Only those namespaced resources
        belonging to a selected namespace are restored.
        """).AddToParser(namespaced_resource_restore_group)
    base.Argument(
        '--selected-applications',
        type=str,
        help="""
        List of selected applications to restore. Only those namespaced
        resources which belong to one of the selected applications are restored.
        """).AddToParser(namespaced_resource_restore_group)
    parser.add_argument(
        '--substitution-rules-file',
        type=str,
        help="""
        If provided, defines a set of resource transformations that will be
        applied to resources from the source backup before they are created in
        the target cluster.
        """)
    parser.add_argument(
        '--description',
        type=str,
        required=False,
        default=None,
        help='Optional text description for the restore.')
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    labels = labels_util.GetUpdateLabelsDictFromArgs(args)
    restore_ref = args.CONCEPTS.restore.Parse()
    restore_config = command_util.GetRestoreConfig(args)
    if args.IsSpecified('async'):
      return api_util.CreateRestore(
          restore_ref,
          backup=args.backup,
          cluster=args.cluster,
          restore_config=restore_config,
          description=args.description,
          labels=labels)
    api_util.CreateRestoreAndWaitForLRO(
        restore_ref,
        backup=args.backup,
        cluster=args.cluster,
        restore_config=restore_config,
        description=args.description,
        labels=labels)
    if not args.IsSpecified('wait_for_completion'):
      return []
    return api_util.WaitForRestoreToFinish(restore_ref.RelativeName())

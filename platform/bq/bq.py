#!/usr/bin/env python
#
# Copyright 2012 Google Inc. All Rights Reserved.
"""Python script for interacting with BigQuery."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import pdb
import sys
import traceback

# Add to path dependencies if present.
_THIRD_PARTY_DIR = os.path.join(os.path.dirname(__file__), 'third_party')
if os.path.isdir(_THIRD_PARTY_DIR) and _THIRD_PARTY_DIR not in sys.path:
  sys.path.insert(0, _THIRD_PARTY_DIR)

# This strange import below ensures that the correct 'google' is imported.
# We reload after sys.path is updated, so we know if we'll find our google
# before any other.
# pylint:disable=g-import-not-at-top
if 'google' in sys.modules:
  import google
  try:
    reload(google)
  except NameError:
    import importlib
    importlib.reload(google)


from absl import flags

from pyglib import appcommands

# pylint: disable=g-bad-import-order

import bigquery_client
import bq_flags
import bq_utils
import credential_loader

from clients import utils as bq_client_utils
from frontend import bigquery_command
from frontend import bq_cached_client
from frontend import commands
from frontend import commands_iam
from frontend import command_copy
from frontend import command_delete
from frontend import command_extract
from frontend import command_info
from frontend import command_list
from frontend import command_load
from frontend import command_make
from frontend import command_mkdef
from frontend import command_query
from frontend import command_repl
from frontend import command_show
from frontend import command_truncate
from frontend import command_update
from frontend import utils as frontend_utils
from utils import bq_id_utils

flags.adopt_module_key_flags(bq_flags)

FLAGS = flags.FLAGS

# TODO(b/324243535): Remove these re-exports once the refactor is complete.
# pylint: disable=protected-access
# pylint: disable=g-bad-name
JobReference = bq_id_utils.ApiClientHelper.JobReference
ProjectReference = bq_id_utils.ApiClientHelper.ProjectReference
DatasetReference = bq_id_utils.ApiClientHelper.DatasetReference
TableReference = bq_id_utils.ApiClientHelper.TableReference
TransferConfigReference = (
    bq_id_utils.ApiClientHelper.TransferConfigReference)
TransferRunReference = bq_id_utils.ApiClientHelper.TransferRunReference
TransferLogReference = bq_id_utils.ApiClientHelper.TransferLogReference
NextPageTokenReference = bq_id_utils.ApiClientHelper.NextPageTokenReference
ModelReference = bq_id_utils.ApiClientHelper.ModelReference
RoutineReference = bq_id_utils.ApiClientHelper.RoutineReference
RowAccessPolicyReference = (
    bq_id_utils.ApiClientHelper.RowAccessPolicyReference)
EncryptionServiceAccount = (
    bq_id_utils.ApiClientHelper.EncryptionServiceAccount)
BigqueryClient = bigquery_client.BigqueryClient
ApiClientHelper = bq_id_utils.ApiClientHelper
JobIdGenerator = bq_client_utils.JobIdGenerator
JobIdGeneratorIncrementing = bq_client_utils.JobIdGeneratorIncrementing
JobIdGeneratorRandom = bq_client_utils.JobIdGeneratorRandom
JobIdGeneratorFingerprint = bq_client_utils.JobIdGeneratorFingerprint
ReservationReference = bq_id_utils.ApiClientHelper.ReservationReference
BetaReservationReference = bq_id_utils.ApiClientHelper.BetaReservationReference
CapacityCommitmentReference = (
    bq_id_utils.ApiClientHelper.CapacityCommitmentReference
)
ReservationAssignmentReference = (
    bq_id_utils.ApiClientHelper.ReservationAssignmentReference
)
BetaReservationAssignmentReference = (
    bq_id_utils.ApiClientHelper.BetaReservationAssignmentReference
)
ConnectionReference = bq_id_utils.ApiClientHelper.ConnectionReference
_FormatDataTransferIdentifiers = bq_id_utils.FormatDataTransferIdentifiers
_FormatProjectIdentifier = bq_id_utils.FormatProjectIdentifier
_PARQUET_LIST_INFERENCE_DESCRIPTION = (
    frontend_utils.PARQUET_LIST_INFERENCE_DESCRIPTION
)
_FormatDataTransferIdentifiers = bq_id_utils.FormatDataTransferIdentifiers
_FormatProjectIdentifier = bq_id_utils.FormatProjectIdentifier
_ValidateGlobalFlags = frontend_utils.ValidateGlobalFlags
ValidateAtMostOneSelected = frontend_utils.ValidateAtMostOneSelected
_UseServiceAccount = bigquery_command._UseServiceAccount
_GetFormatterFromFlags = frontend_utils.GetFormatterFromFlags
_PrintDryRunInfo = frontend_utils.PrintDryRunInfo
_GetJobIdFromFlags = frontend_utils.GetJobIdFromFlags
_GetWaitPrinterFactoryFromFlags = (
    bq_cached_client._GetWaitPrinterFactoryFromFlags
)
_RawInput = frontend_utils.RawInput
_PromptWithDefault = frontend_utils.PromptWithDefault
_PromptYN = frontend_utils.PromptYN
_NormalizeFieldDelimiter = frontend_utils.NormalizeFieldDelimiter
_ValidateHivePartitioningOptions = (
    frontend_utils.ValidateHivePartitioningOptions
)
_ParseLabels = frontend_utils.ParseLabels
IsRangeBoundaryUnbounded = frontend_utils.IsRangeBoundaryUnbounded
_ParseRangeString = frontend_utils.ParseRangeString
TablePrinter = frontend_utils.TablePrinter
# TODO(b/324243535): Migrate these. They are used a lot in test.
Factory = bq_cached_client.Factory
Client = bq_cached_client.Client
NewCmd = bigquery_command.NewCmd
BigqueryCmd = bigquery_command.BigqueryCmd
_Load = command_load.Load
_CreateExternalTableDefinition = frontend_utils.CreateExternalTableDefinition
_MakeExternalTableDefinition = command_mkdef.MakeExternalTableDefinition
_Query = command_query.Query
_Extract = command_extract.Extract
_Partition = commands.Partition
_List = command_list.ListCmd
_PrintPageToken = frontend_utils.PrintPageToken
_Delete = command_delete.Delete
_Copy = command_copy.Copy
_ParseTimePartitioning = frontend_utils.ParseTimePartitioning
_ParseFileSetSpecType = frontend_utils.ParseFileSetSpecType
_ParseClustering = frontend_utils.ParseClustering
_ParseNumericTypeConversionMode = frontend_utils.ParseNumericTypeConversionMode
_ParseRangePartitioning = frontend_utils.ParseRangePartitioning
_Make = command_make.Make
_Truncate = command_truncate.Truncate
_Update = command_update.Update
_Show = command_show.Show
_IsSuccessfulDmlOrDdlJob = frontend_utils.IsSuccessfulDmlOrDdlJob
_MaybeGetSessionTempObjectName = frontend_utils.MaybeGetSessionTempObjectName
_PrintJobMessages = frontend_utils.PrintJobMessages
_PrintObjectInfo = frontend_utils.PrintObjectInfo
_PrintObjectsArray = frontend_utils.PrintObjectsArray
_PrintObjectsArrayWithToken = frontend_utils.PrintObjectsArrayWithToken
_Cancel = commands.Cancel
_Head = commands.Head
_Insert = commands.Insert
_Wait = commands.Wait
_IamPolicyCmd = commands_iam._IamPolicyCmd
_GetIamPolicy = commands_iam.GetIamPolicy
_SetIamPolicy = commands_iam.SetIamPolicy
_IamPolicyBindingCmd = commands_iam._IamPolicyBindingCmd
_AddIamPolicyBinding = commands_iam.AddIamPolicyBinding
_RemoveIamPolicyBinding = commands_iam.RemoveIamPolicyBinding
# pylint: enable=protected-access
# pylint: enable=g-bad-name


# pylint: enable=g-bad-name

# TODO(b/324243535): Remove these re-exports as a final step.
_Repl = command_repl.Repl
_Init = commands.Init
_Version = commands.Version
_Info = command_info.Info
_ParseUdfResources = frontend_utils.ParseUdfResources
ValidateDatasetName = frontend_utils.ValidateDatasetName
_ParseParameters = frontend_utils.ParseParameters
_SplitParam = frontend_utils.SplitParam
_ParseParameter = frontend_utils.ParseParameter
_ParseParameterTypeAndValue = frontend_utils.ParseParameterTypeAndValue
_ParseParameterType = frontend_utils.ParseParameterType
_ParseStructType = frontend_utils.ParseStructType
_StructTypeSplit = frontend_utils.StructTypeSplit
_FormatRfc3339 = frontend_utils.FormatRfc3339
_ParseRangeParameterValue = frontend_utils.ParseRangeParameterValue
_ParseParameterValue = frontend_utils.ParseParameterValue


def main(unused_argv):
  # Avoid using global flags in main(). In this command line:
  # bq <global flags> <command> <global and local flags> <command args>,
  # only "<global flags>" will parse before main, not "<global and local flags>"


  try:
    frontend_utils.ValidateGlobalFlags()

    bq_commands = {
        # Keep the commands alphabetical.
        'add-iam-policy-binding': commands_iam.AddIamPolicyBinding,
        'cancel': commands.Cancel,
        'cp': command_copy.Copy,
        'extract': command_extract.Extract,
        'get-iam-policy': commands_iam.GetIamPolicy,
        'head': commands.Head,
        'info': command_info.Info,
        'init': commands.Init,
        'insert': commands.Insert,
        'load': command_load.Load,
        'ls': command_list.ListCmd,
        'mk': command_make.Make,
        'mkdef': command_mkdef.MakeExternalTableDefinition,
        'partition': commands.Partition,
        'query': command_query.Query,
        'remove-iam-policy-binding': commands_iam.RemoveIamPolicyBinding,
        'rm': command_delete.Delete,
        'set-iam-policy': commands_iam.SetIamPolicy,
        'shell': command_repl.Repl,
        'show': command_show.Show,
        'truncate': command_truncate.Truncate,
        'update': command_update.Update,
        'version': commands.Version,
        'wait': commands.Wait,
    }

    for command, function in bq_commands.items():
      if command not in appcommands.GetCommandList():
        appcommands.AddCmd(command, function)

  except KeyboardInterrupt as e:
    print('Control-C pressed, exiting.')
    sys.exit(1)
  except BaseException as e:  # pylint: disable=broad-except
    print('Error initializing bq client: %s' % (e,))
    # Use global flags if they're available, but we're exitting so we can't
    # count on global flag parsing anyways.
    if FLAGS.debug_mode or FLAGS.headless:
      traceback.print_exc()
      if not FLAGS.headless:
        pdb.post_mortem()
    sys.exit(1)


# pylint: disable=g-bad-name
def run_main():
  """Function to be used as setuptools script entry point.

  Appcommands assumes that it always runs as __main__, but launching
  via a setuptools-generated entry_point breaks this rule. We do some
  trickery here to make sure that appcommands and flags find their
  state where they expect to by faking ourselves as __main__.
  """

  # Put the flags for this module somewhere the flags module will look
  # for them.
  new_name = sys.argv[0]
  sys.modules[new_name] = sys.modules['__main__']
  for flag in FLAGS.flags_by_module_dict().get(__name__, []):
    FLAGS.register_flag_by_module(new_name, flag)
    for key_flag in FLAGS.key_flags_by_module_dict().get(__name__, []):
      FLAGS.register_key_flag_for_module(new_name, key_flag)

  # Now set __main__ appropriately so that appcommands will be
  # happy.
  sys.modules['__main__'] = sys.modules[__name__]
  appcommands.Run()
  sys.modules['__main__'] = sys.modules.pop(new_name)


if __name__ == '__main__':
  appcommands.Run()

#!/usr/bin/env python
"""Legacy file reexporting previous Bigquery Client entry points."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function



from clients import bigquery_client
from clients import bigquery_client_extended
from clients import bigquery_http
from clients import table_reader as bq_table_reader
from clients import utils as bq_client_utils
from utils import bq_id_utils
from utils import bq_processor_utils

# TODO(b/324243535): Delete these once the migration is complete.
# pylint: disable=protected-access
AUTHORIZATION_CODE = bigquery_client_extended.AUTHORIZATION_CODE
VERSION_INFO = bigquery_client_extended.VERSION_INFO
MakeAccessRolePropertiesJson = bq_processor_utils.MakeAccessRolePropertiesJson
MakeTenantIdPropertiesJson = bq_processor_utils.MakeTenantIdPropertiesJson
MakeAzureFederatedAppClientIdPropertiesJson = (
    bq_processor_utils.MakeAzureFederatedAppClientIdPropertiesJson
)
MakeAzureFederatedAppClientAndTenantIdPropertiesJson = (
    bq_processor_utils.MakeAzureFederatedAppClientAndTenantIdPropertiesJson
)
_ToLowerCamel = bq_processor_utils.ToLowerCamel
_ApplyParameters = bq_processor_utils.ApplyParameters
_FormatProjectIdentifierForTransfers = (
    bq_processor_utils.FormatProjectIdentifierForTransfers
)
_ParseJson = bq_processor_utils.ParseJson
InsertEntry = bq_processor_utils.InsertEntry
JsonToInsertEntry = bq_processor_utils.JsonToInsertEntry
_PrintFormattedJsonObject = bq_client_utils._PrintFormattedJsonObject
MaybePrintManualInstructionsForConnection = (
    bq_client_utils.MaybePrintManualInstructionsForConnection
)
_ToFilename = bq_client_utils._ToFilename
_OverwriteCurrentLine = bq_client_utils._OverwriteCurrentLine
_FormatLabels = bq_client_utils._FormatLabels
_FormatTableReference = bq_client_utils._FormatTableReference
_FormatTags = bq_client_utils._FormatTags
_FormatResourceTags = bq_client_utils._FormatResourceTags
_FormatStandardSqlFields = bq_client_utils._FormatStandardSqlFields
_ParseJobIdentifier = bq_client_utils._ParseJobIdentifier
_ParseReservationIdentifier = bq_client_utils._ParseReservationIdentifier
_ParseReservationPath = bq_client_utils.ParseReservationPath
_ParseCapacityCommitmentIdentifier = (
    bq_client_utils._ParseCapacityCommitmentIdentifier
)
_ParseCapacityCommitmentPath = bq_client_utils.ParseCapacityCommitmentPath
_ParseReservationAssignmentIdentifier = (
    bq_client_utils._ParseReservationAssignmentIdentifier
)
_ParseReservationAssignmentPath = (
    bq_client_utils._ParseReservationAssignmentPath
)
_ParseConnectionIdentifier = bq_client_utils._ParseConnectionIdentifier
_ParseConnectionPath = bq_client_utils._ParseConnectionPath
ReadTableConstrants = bq_client_utils.ReadTableConstrants
BigqueryModel = bigquery_http.BigqueryModel
BigqueryHttp = bigquery_http.BigqueryHttp
JobIdGenerator = bq_client_utils.JobIdGenerator
JobIdGeneratorNone = bq_client_utils.JobIdGeneratorNone
JobIdGeneratorRandom = bq_client_utils.JobIdGeneratorRandom
JobIdGeneratorFingerprint = bq_client_utils.JobIdGeneratorFingerprint
JobIdGeneratorIncrementing = bq_client_utils.JobIdGeneratorIncrementing
TransferScheduleArgs = bigquery_client_extended.TransferScheduleArgs
BigqueryClient = bigquery_client_extended.BigqueryClientExtended
_TableReader = bq_table_reader._TableReader
_TableTableReader = bq_table_reader.TableTableReader
_JobTableReader = bq_table_reader.JobTableReader
_QueryTableReader = bq_table_reader.QueryTableReader
# pylint: enable=protected-access

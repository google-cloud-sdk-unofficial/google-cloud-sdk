# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Lists users in a given project.

Lists users in a given project in the alphabetical order of the user name.
"""


from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times


def _TransformCredentialAuditFindings(findings, undefined=""):
  """Formats credential audit findings as a list of single-line strings.

  Each finding is formatted as `RESULT (STATE, LAST_DETECT_TIME)`, e.g.
  `CREDENTIALS_LEAKED (ACTIVE, 2026-10-21T10:00:00.500Z)`.

  Args:
    findings: A list of serialized security findings.
    undefined: Returns this value if there are no findings.

  Returns:
    The formatted findings separated by "; ", or undefined if there are none.
  """
  if not findings:
    return undefined
  formatted = []
  for finding in findings:
    result = (finding.get("result") or {}).get(
        "credentialAuditFinding", "CREDENTIAL_AUDIT_FINDING_UNSPECIFIED"
    )
    details = [finding.get("state", "STATE_UNSPECIFIED")]
    if finding.get("lastDetectTime"):
      details.append(finding["lastDetectTime"])
    formatted.append("{} ({})".format(result, ", ".join(details)))
  return "; ".join(formatted)


def AddBaseArgs(parser):
  flags.AddInstance(parser)
  flags.AddUserView(parser)
  parser.display_info.AddCacheUpdater(flags.UserCompleter)
  parser.display_info.AddTransforms(
      {"credential_audit_findings": _TransformCredentialAuditFindings}
  )


def _KeepCredentialAuditFindings(user, sql_messages):
  """Keeps all of the user's credential audit findings, with their details.

  Findings of all states (active and closed) are kept, ordered from the most
  recently detected to the least recently detected.

  Args:
    user: The SQL user resource, modified in place.
    sql_messages: The SQL API messages module.
  """
  credential_audit_type = (
      sql_messages.SecurityFinding.FindingTypeValueValuesEnum.CREDENTIAL_AUDIT
  )
  epoch = times.GetDateTimeFromTimeStamp(0, tzinfo=times.UTC)
  user.securityFindings = sorted(
      (
          finding
          for finding in user.securityFindings
          if finding.findingType == credential_audit_type
      ),
      key=lambda finding: (
          times.ParseDateTime(finding.lastDetectTime, tzinfo=times.UTC)
          if finding.lastDetectTime
          else epoch
      ),
      reverse=True,
  )


def RunBaseListCommand(args, release_track):
  """Lists Cloud SQL users in a given instance.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked with.
    release_track: base.ReleaseTrack, the release track that this was run under.

  Returns:
    SQL user resource iterator.
  """
  client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
  sql_client = client.sql_client
  sql_messages = client.sql_messages

  project_id = properties.VALUES.core.project.Get(required=True)

  users = sql_client.users.List(
      sql_messages.SqlUsersListRequest(
          project=project_id,
          instance=args.instance,
          view=flags.GetUserView(
              args.view, sql_messages.SqlUsersListRequest.ViewValueValuesEnum
          ),
      )
  ).items

  # We will not display dual passwords if no user in the instance
  # has information about this field. This an implicit way of saying that we
  # will only show dual password type on MySQL 8.0, as no other instance type
  # will have dual password information. Likewise, we will not display
  # IAM status if no user in the instance has information about this field.
  dual_password_type = ""
  iam_status = ""
  for user in users:
    if user.dualPasswordType:
      dual_password_type = "dualPasswordType,"
    policy = user.passwordPolicy
    if (
        user.iamStatus
        == sql_messages.User.IamStatusValueValuesEnum.IAM_STATUS_UNSPECIFIED
    ):
      user.iamStatus = None
    if user.iamStatus:
      iam_status = "iamStatus,"
    if args.view == "full":
      _KeepCredentialAuditFindings(user, sql_messages)
    if not policy:
      continue
    # Don't display
    policy.enableFailedAttemptsCheck = None

  # Show all of each user's credential audit findings, each flattened to
  # `RESULT (STATE, LAST_DETECT_TIME)`, when security findings are requested.
  security_findings = ""
  if args.view == "full":
    security_findings = (
        "securityFindings.credential_audit_findings():"
        "label=CREDENTIAL_AUDIT_FINDING,"
    )

  # Dual Password types is exposed in all release tracks, but we will not
  # expose the column early to customers, because returning the Dual Password
  # status is gated by a flag upstream.
  if release_track == base.ReleaseTrack.GA:
    # Because there are tests running against Python 3.5, I can't use f-Strings.
    args.GetDisplayInfo().AddFormat(
        """
      table(
        name.yesno(no='(anonymous)'),
        host,
        type.yesno(no='BUILT_IN'),
        {dualPasswordType}
        {iamStatus}
        {securityFindings}
        passwordPolicy
      )
    """.format(
            dualPasswordType=dual_password_type,
            iamStatus=iam_status,
            securityFindings=security_findings,
        )
    )
  else:
    args.GetDisplayInfo().AddFormat(
        """
      table(
        name.yesno(no='(anonymous)'),
        host,
        type.yesno(no='BUILT_IN'),
        {dualPasswordType}
        {iamStatus}
        iamEmail,
        {securityFindings}
        passwordPolicy
      )
    """.format(
            dualPasswordType=dual_password_type,
            iamStatus=iam_status,
            securityFindings=security_findings,
        )
    )

  return users


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.UniverseCompatible
class List(base.ListCommand):
  """Lists Cloud SQL users in a given instance.

  Lists Cloud SQL users in a given instance in the alphabetical
  order of the user name.
  """

  @staticmethod
  def Args(parser):
    AddBaseArgs(parser)

  def Run(self, args):
    return RunBaseListCommand(args, self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.UniverseCompatible
class ListBeta(List):
  """Lists Cloud SQL users in a given instance.

  Lists Cloud SQL users in a given instance in the alphabetical
  order of the user name.
  """

  @staticmethod
  def Args(parser):
    AddBaseArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class ListAlpha(ListBeta):
  """Lists Cloud SQL users in a given instance.

  Lists Cloud SQL users in a given instance in the alphabetical
  order of the user name.
  """

  @staticmethod
  def Args(parser):
    AddBaseArgs(parser)

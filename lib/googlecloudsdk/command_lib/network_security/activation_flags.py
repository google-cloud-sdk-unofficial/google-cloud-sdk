# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Flags for Firewall Plus Endpoint commands."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from googlecloudsdk.api_lib.network_security.firewall_endpoints import activation_api
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps as deps_lib
from googlecloudsdk.calliope.concepts import multitype
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties


ENDPOINT_RESOURCE_NAME = "FIREWALL_ENDPOINT"
ORG_ENDPOINT_RESOURCE_COLLECTION = (
    "networksecurity.organizations.locations.firewallEndpoints"
)
PROJECT_ENDPOINT_RESOURCE_COLLECTION = (
    "networksecurity.projects.locations.firewallEndpoints"
)
BILLING_HELP_TEST = (
    "The Google Cloud project ID to use for API enablement check, quota, and"
    " endpoint uptime billing."
)


def OrgEndpointResourceSpec(api_version):
  """Returns the resource spec for an organization level firewall endpoint."""
  return concepts.ResourceSpec(
      ORG_ENDPOINT_RESOURCE_COLLECTION,
      "firewall endpoint",
      api_version=api_version,
      organizationsId=concepts.ResourceParameterAttributeConfig(
          "organization",
          "Organization ID of the {resource}.",
          parameter_name="organizationsId",
      ),
      locationsId=concepts.ResourceParameterAttributeConfig(
          "zone",
          "Zone of the {resource}.",
          parameter_name="locationsId",
          fallthroughs=[
              deps_lib.ArgFallthrough("--location"),
          ],
      ),
      firewallEndpointsId=concepts.ResourceParameterAttributeConfig(
          "endpoint-name",
          "Name of the {resource}",
          parameter_name="firewallEndpointsId",
      ),
  )


def ProjectEndpointResourceSpec(api_version):
  """Returns the resource spec for a project level firewall endpoint."""
  return concepts.ResourceSpec(
      PROJECT_ENDPOINT_RESOURCE_COLLECTION,
      "firewall endpoint",
      api_version=api_version,
      projectsId=concepts.ResourceParameterAttributeConfig(
          name="project",
          help_text=(
              "Project ID of the Google Cloud project for the {resource}."
          ),
          fallthroughs=[
              # Do not fallthrough to the --project flag, as this will prompt
              # the user to choose between project and org scoped endpoints when
              # supplying both --organization and --project.
              deps_lib.PropertyFallthrough(properties.VALUES.core.project),
          ],
      ),
      locationsId=concepts.ResourceParameterAttributeConfig(
          "zone",
          "Zone of the {resource}.",
          parameter_name="locationsId",
          fallthroughs=[
              deps_lib.ArgFallthrough("--location"),
          ],
      ),
      firewallEndpointsId=concepts.ResourceParameterAttributeConfig(
          "endpoint-name",
          "Name of the {resource}",
          parameter_name="firewallEndpointsId",
      ),
  )


def AddEndpointResource(release_track, parser, project_scope_supported=False):
  """Adds Firewall Plus endpoint resource."""
  api_version = activation_api.GetApiVersion(release_track)
  concept_specs = [
      OrgEndpointResourceSpec(api_version),
  ]
  if project_scope_supported:
    concept_specs.append(ProjectEndpointResourceSpec(api_version))
  resource_spec = multitype.MultitypeResourceSpec(
      "firewall endpoint",
      *concept_specs,
      allow_inactive=True,
  )
  presentation_spec = presentation_specs.MultitypeResourcePresentationSpec(
      name=ENDPOINT_RESOURCE_NAME,
      concept_spec=resource_spec,
      required=True,
      group_help="Firewall Plus.",
  )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddMaxWait(
    parser,
    default_max_wait,
    help_text="Time to synchronously wait for the operation to complete, after which the operation continues asynchronously. Ignored if --no-async isn't specified. See $ gcloud topic datetimes for information on time formats.",
):
  """Adds --max-wait flag."""
  parser.add_argument(
      "--max-wait",
      dest="max_wait",
      required=False,
      default=default_max_wait,
      help=help_text,
      type=arg_parsers.Duration(),
  )


def MakeGetUriFunc(release_track):
  return (
      lambda x: activation_api.GetEffectiveApiEndpoint(release_track) + x.name
  )


def AddOrganizationArg(parser, help_text="Organization of the endpoint"):
  parser.add_argument("--organization", required=True, help=help_text)


def AddDescriptionArg(parser, help_text="Description of the endpoint"):
  parser.add_argument("--description", required=False, help=help_text)


def AddLocationArg(
    parser, required=False, help_text="Location of the endpoint"
):
  parser.add_argument("--location", required=required, help=help_text)


def AddTargetFirewallAttachmentArg(
    parser,
    help_text="Target firewall attachment where third party endpoint forwards traffic."
):
  parser.add_argument(
      "--target-firewall-attachment", required=False, help=help_text
  )


def AddEnableJumboFramesArg(
    parser,
    required=False,
    help_text="Enable jumbo frames for the firewall endpoint. To disable jumbo frames, use --no-enable-jumbo-frames.",
):
  parser.add_argument(
      "--enable-jumbo-frames",
      required=required,
      help=help_text,
      action="store_true",
  )


def AddZoneArg(parser, required=True, help_text="Zone of the endpoint"):
  parser.add_argument("--zone", required=required, help=help_text)


def AddBillingProjectArg(
    parser,
    required=True,
    help_text=BILLING_HELP_TEST,
):
  """Add billing project argument to parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
    required: bool, whether to make this argument required.
    help_text: str, help text to overwrite the generic --billing-project help
      text.
  """
  parser.add_argument(
      "--billing-project",
      required=required,
      help=help_text,
      action=actions.StoreProperty(properties.VALUES.billing.quota_project),
  )


# We use the explicit --update-billing-project flag as opposed to the existent
# --billing-project flag because otherwise there will be an ambiguity when a
# user wants to update other things, but not the billing project.
# For example, to update the labels, a billing project is still needed for API
# quota, making the ambiguous call:
# gcloud network-security firewall-endpoints update \
#     --billing-project=proj --update-labels=k1=v1
# This is a common use for other gcloud update flags as well.
def AddUpdateBillingProjectArg(
    parser,
    required=False,
    help_text=BILLING_HELP_TEST,
):
  """Add update billing project argument to parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
    required: bool, whether to make this argument required.
    help_text: str, help text to display on the --update-billing-project help
      text.
  """
  parser.add_argument(
      "--update-billing-project",
      required=required,
      help=help_text,
      metavar="BILLING_PROJECT",
      action=actions.StoreProperty(properties.VALUES.billing.quota_project),
  )


def AddEnableWildfireArg(
    parser,
):
  """Adds --enable-wildfire flag.

  It corresponds to the proto field:
  google.cloud.networksecurity.v1main.FirewallEndpoint.WildfireSettings.enabled

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      "--enable-wildfire",
      action="store_true",
      required=False,
      help=(
          "Enable WildFire functionality on the endpoint. Use"
          " --enable-wildfire to enable. To disable, use --no-enable-wildfire."
      ),
  )


def AddWildfireRegionArg(
    parser,
):
  """Adds --wildfire-region flag."""
  parser.add_argument(
      "--wildfire-region",
      required=False,
      help=(
          "The region WildFire submissions from this endpoint will be sent to"
          " for analysis by WildFire. Defaults to the nearest available region."
      ),
  )


def AddContentCloudRegionArg(
    parser,
):
  """Adds --content-cloud-region flag."""
  parser.add_argument(
      "--content-cloud-region",
      required=False,
      help=(
          "The content cloud region the endpoint will use. Defaults to the"
          " nearest available region."
      ),
  )


def AddWildfireLookupTimeoutArg(
    parser,
):
  """Adds --wildfire-lookup-timeout flag.

  It corresponds to the proto field:
  google.cloud.networksecurity.v1main.FirewallEndpoint.WildfireSettings
  .wildfire_realtime_lookup_duration.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      "--wildfire-lookup-timeout",
      type=int,
      required=False,
      help=(
          "The timeout (in milliseconds) to hold a file while the WildFire real"
          " time signature cloud performs a signature lookup."
      ),
  )


def AddWildfireLookupActionArg(
    parser,
):
  """Adds --wildfire-lookup-action flag.

  It corresponds to the proto field:
  google.cloud.networksecurity.v1main.FirewallEndpoint.WildfireSettings
  .wildfire_realtime_lookup_timeout_action.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      "--wildfire-lookup-action",
      choices=["ALLOW", "DENY"],
      required=False,
      help=(
          "The action to take on WildFire real time signature lookup timeout."
      ),
  )


def AddWildfireAnalysisTimeoutArg(
    parser,
):
  """Adds --wildfire-analysis-timeout flag.

  It corresponds to the proto field:
  google.cloud.networksecurity.v1main.FirewallEndpoint.WildfireSettings.WildfireInlineCloudAnalysisSettings
  .max_analysis_duration.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      "--wildfire-analysis-timeout",
      type=int,
      required=False,
      help=(
          "The timeout (in milliseconds) on a file being held while WildFire"
          " inline cloud analysis is performed."
      ),
  )


def AddWildfireAnalysisActionArg(
    parser,
):
  """Adds --wildfire-analysis-action flag.

  It corresponds to the proto field:
  google.cloud.networksecurity.v1main.FirewallEndpoint.WildfireSettings.WildfireInlineCloudAnalysisSettings.timeout_action.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      "--wildfire-analysis-action",
      choices=["ALLOW", "DENY"],
      required=False,
      help="The action to take on WildFire inline cloud analysis timeout.",
  )


def AddEnableWildfireAnalysisLoggingArg(
    parser,
):
  """Adds enable-wildfire-analysis-logging flag.

  It corresponds to the proto field:
  google.cloud.networksecurity.v1main.FirewallEndpoint.WildfireSettings.WildfireInlineCloudAnalysisSettings
  .timeout_logging_disabled.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      "--enable-wildfire-analysis-logging",
      action="store_true",
      required=False,
      help=(
          "Enable WildFire inline cloud analysis submission timeout logging."
          " This is enabled by default. Use"
          " `--no-enable-wildfire-analysis-logging` to disable."
      ),
  )


def AddBlockPartialHttpArg(
    parser,
):
  """Adds --block-partial-http flag.

  It corresponds to the proto field:
  google.cloud.networksecurity.v1main.FirewallEndpoint.EndpointSettings
  .http_partial_response_blocked.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      "--block-partial-http",
      action="store_true",
      required=False,
      help=(
          "Block HTTP partial responses. Defaults to false. Use"
          " `--block-partial-http` to enable. To disable, use"
          " `--no-block-partial-http`."
      ),
  )


def _ExtractResourceSegment(
    path_segments: Sequence[str], collection_name: str
) -> str | None:
  """Returns the segment immediately following collection_name in path segments."""
  target = collection_name.lower()
  for i, segment in enumerate(path_segments[:-1]):
    if segment.lower() == target:
      return path_segments[i + 1]
  return None


def _StripResourcePrefix(
    value: str | None,
    collection_name: str,
    *,
    strip_parent_path: bool = False,
) -> str | None:
  """Strips resource collection prefix or full parent path from a resource name.

  Args:
    value: The resource name or path to clean.
    collection_name: The collection name (e.g. 'cryptoKeys', 'keyrings').
    strip_parent_path: If True, strips parent path segments to return only the
      resource ID. If False, only strips the immediate collection prefix for
      short names, preserving full resource paths.

  Returns:
    The cleaned resource name, or None/empty string if input was None/empty.
  """
  if not value or not isinstance(value, str):
    return value
  cleaned = value.strip().rstrip("/")
  if not cleaned:
    return value
  if strip_parent_path:
    segments = cleaned.split("/")
    return _ExtractResourceSegment(segments, collection_name) or segments[-1]
  target_prefix = f"{collection_name.lower()}/"
  if cleaned.lower().startswith(target_prefix):
    return cleaned[len(target_prefix) :].split("/")[0]
  return cleaned


def _StripCryptoKeyPrefix(
    key_name: str | None,
) -> str | None:
  """Strips cryptoKeys/ prefix if present on short key names."""
  return _StripResourcePrefix(
      key_name, "cryptoKeys", strip_parent_path=False
  )


def _StripKeyringPrefix(
    keyring_name: str | None,
) -> str | None:
  """Strips keyRings/ and parent path prefixes if present on keyring names."""
  return _StripResourcePrefix(
      keyring_name, "keyrings", strip_parent_path=True
  )


def _DeriveRegionFromZone(zone_or_location: str) -> str:
  """Derives a region from a zone name or path."""
  zone_name = zone_or_location.strip().rstrip("/").split("/")[-1]
  region, sep, zone_suffix = zone_name.rpartition("-")
  if sep and len(zone_suffix) == 1 and zone_suffix.isalpha():
    return region
  return zone_name


class ZoneToRegionFallthrough(deps_lib.ArgFallthrough):
  """Fallthrough to derive KMS region from endpoint --zone or --location."""

  def __init__(self):
    """Initializes the ZoneToRegionFallthrough."""
    super().__init__("--zone")
    self._hint = (
        "provide the argument `--zone` or `--kms-location` on the command line"
    )

  def _Call(self, parsed_args: argparse.Namespace) -> str | None:
    """See base class."""
    for candidate in (
        super()._Call(parsed_args),
        getattr(parsed_args, "location", None),
    ):
      if candidate and str(candidate).strip():
        return _DeriveRegionFromZone(str(candidate))

    try:
      property_zone = properties.VALUES.compute.zone.Get()
      if property_zone and str(property_zone).strip():
        return _DeriveRegionFromZone(str(property_zone))
    except properties.Error:
      # Property could not be read or is invalid; fall through to returning
      # None.
      pass

    return None


class _KeyringAttributeFallthrough(deps_lib.ArgFallthrough):
  """Base fallthrough to extract an attribute from a --kms-keyring argument."""

  def __init__(self, collection_name: str):
    """Initializes the _KeyringAttributeFallthrough."""
    super().__init__("--kms-keyring")
    self._collection_name = collection_name

  def _Call(self, parsed_args: argparse.Namespace) -> str | None:
    """See base class."""
    keyring = super()._Call(parsed_args)
    if not keyring or not isinstance(keyring, str):
      return None
    keyring_trimmed = keyring.strip()
    if not keyring_trimmed:
      return None
    segments = keyring_trimmed.rstrip("/").split("/")
    return _ExtractResourceSegment(segments, self._collection_name)


class KeyringLocationFallthrough(_KeyringAttributeFallthrough):
  """Fallthrough to extract location from a full --kms-keyring path."""

  def __init__(self):
    """Initializes the KeyringLocationFallthrough."""
    super().__init__(collection_name="locations")


class KeyringProjectFallthrough(_KeyringAttributeFallthrough):
  """Fallthrough to extract project from a full --kms-keyring path."""

  def __init__(self):
    """Initializes the KeyringProjectFallthrough."""
    super().__init__(collection_name="projects")


def KmsKeyringAttributeConfig() -> concepts.ResourceParameterAttributeConfig:
  """Returns the ResourceParameterAttributeConfig for the KMS keyring."""
  return concepts.ResourceParameterAttributeConfig(
      name="kms-keyring",
      help_text="The KMS keyring of the {resource}.",
  )


def KmsLocationAttributeConfig() -> concepts.ResourceParameterAttributeConfig:
  """Returns the ResourceParameterAttributeConfig for the KMS location."""
  return concepts.ResourceParameterAttributeConfig(
      name="kms-location",
      help_text=(
          "The Google Cloud location for the {resource}. Defaults to the"
          " region derived from the endpoint --zone to satisfy Cloud NGFW"
          " Enterprise regional co-location requirements."
      ),
      fallthroughs=[
          KeyringLocationFallthrough(),
          ZoneToRegionFallthrough(),
      ],
  )


def KmsProjectAttributeConfig() -> concepts.ResourceParameterAttributeConfig:
  """Returns the ResourceParameterAttributeConfig for the KMS project."""
  return concepts.ResourceParameterAttributeConfig(
      name="kms-project",
      help_text="The Google Cloud project for the {resource}.",
      fallthroughs=[
          KeyringProjectFallthrough(),
          deps_lib.ArgFallthrough("--project"),
          deps_lib.PropertyFallthrough(properties.VALUES.core.project),
      ],
  )


def KmsKeyResourceSpec() -> concepts.ResourceSpec:
  """Returns the ResourceSpec for the Cloud KMS cryptokey."""
  return concepts.ResourceSpec(
      "cloudkms.projects.locations.keyRings.cryptoKeys",
      resource_name="key",
      cryptoKeysId=concepts.ResourceParameterAttributeConfig(
          name="kms-key",
          help_text="The KMS key of the {resource}.",
          value_type=_StripCryptoKeyPrefix,
      ),
      keyRingsId=KmsKeyringAttributeConfig(),
      locationsId=KmsLocationAttributeConfig(),
      projectsId=KmsProjectAttributeConfig(),
      disable_auto_completers=False,
  )


_KMS_FLAG_NAMES = ("kms_key", "kms_keyring", "kms_location", "kms_project")


def _IsKmsFlagSpecified(args: argparse.Namespace, flag: str) -> bool:
  """Returns True if the KMS flag was specified in the parsed args.

  Args:
    args: The parsed command-line arguments.
    flag: The destination name of the flag to check.

  Returns:
    True if the flag was specified on the command line or has a non-None value.
  """
  is_specified = getattr(args, "IsSpecified", None)
  if callable(is_specified) and hasattr(args, flag):
    return is_specified(flag)
  return getattr(args, flag, None) is not None


def HasKmsArgs(args: argparse.Namespace) -> bool:
  """Returns True if any KMS argument was specified in the parsed args.

  Args:
    args: The parsed command-line arguments.

  Returns:
    True if any KMS argument was specified.
  """
  return any(_IsKmsFlagSpecified(args, flag) for flag in _KMS_FLAG_NAMES)


def GetSpecifiedKmsFlag(args: argparse.Namespace) -> str:
  """Returns the CLI flag name of the first specified KMS argument.

  Args:
    args: The parsed command-line arguments.

  Returns:
    The CLI flag name (e.g. '--kms-key', '--kms-keyring') or '--kms-key'.
  """
  for flag in _KMS_FLAG_NAMES:
    if _IsKmsFlagSpecified(args, flag):
      flag_name = flag.replace("_", "-")
      return f"--{flag_name}"
  return "--kms-key"


def GetAndValidateKmsKeyName(args: argparse.Namespace) -> str | None:
  """Parses and validates the KMS key resource argument.

  Args:
    args: The parsed command-line arguments.

  Returns:
    The fully-qualified KMS key relative name, or None if no KMS flags
    were specified.

  Raises:
    exceptions.InvalidArgumentException: If KMS arguments were specified but
      failed to parse into a valid fully-qualified KMS key.
  """
  kms_ref = None
  concepts_holder = getattr(args, "CONCEPTS", None)
  kms_concept = getattr(concepts_holder, "kms_key", None)
  if kms_concept is not None:
    try:
      kms_ref = kms_concept.Parse()
    except concepts.InitializationError:
      kms_ref = None

  if kms_ref:
    keyring_id = getattr(kms_ref, "keyRingsId", None)
    clean_keyring = _StripKeyringPrefix(keyring_id)
    if clean_keyring and clean_keyring != keyring_id:
      clean_crypto_key = _StripCryptoKeyPrefix(
          getattr(kms_ref, "cryptoKeysId", None)
      ) or kms_ref.cryptoKeysId
      return (
          f"projects/{kms_ref.projectsId}/locations/{kms_ref.locationsId}/"
          f"keyRings/{clean_keyring}/cryptoKeys/{clean_crypto_key}"
      )
    return kms_ref.RelativeName()

  # If parsing failed but KMS args were specified, raise error.
  if HasKmsArgs(args):
    raise exceptions.InvalidArgumentException(
        "--kms-project --kms-location --kms-keyring --kms-key",
        "Specify fully qualified KMS key ID with --kms-key, or use "
        "combination of --kms-project, --kms-location, --kms-keyring and "
        "--kms-key to specify the key ID in pieces.",
    )
  return None


def AddKmsKeyArg(
    parser: parser_arguments.ArgumentInterceptor,
    release_track: base.ReleaseTrack,
    hidden: bool = True,
) -> None:
  """Adds --kms-key flag for Firewall Plus endpoints.

  Args:
    parser: An argparse parser.
    release_track: The release track of the command.
    hidden: Whether to hide this argument.
  """
  if release_track not in (base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA):
    return
  permission_info = (
      "The 'Network Security Service Agent' service account must hold"
      " permission 'Cloud KMS CryptoKey Encrypter/Decrypter'"
  )
  group_help = (
      "The Cloud KMS (Key Management Service) cryptokey that will be"
      f" used to protect the firewall endpoint. {permission_info}."
  )
  concept_parsers.ConceptParser.ForResource(
      "--kms-key",
      KmsKeyResourceSpec(),
      group_help,
      required=False,
      hidden=hidden,
  ).AddToParser(parser)

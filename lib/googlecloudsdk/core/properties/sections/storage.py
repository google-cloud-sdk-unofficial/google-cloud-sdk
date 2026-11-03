# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Contains the properties for the 'storage' section."""

import enum
import textwrap

from googlecloudsdk.core.properties.providers import PROVIDERS
from googlecloudsdk.core.properties.types import _Section
from googlecloudsdk.core.properties.validators import _HumanReadableByteAmountValidator
from googlecloudsdk.core.properties.validators import _IntegerValidator


class _SectionStorage(_Section):
  """Contains the properties for the 'storage' section."""

  _CHECK_HASHES_HELP_TEXT = textwrap.dedent("""\
      'check_hashes' specifies how strictly to require integrity checking for
      downloaded data. Legal values are:
      +
      * 'if_fast_else_fail' - (default) Only integrity check if the digest
      will run efficiently (using compiled code), else fail the download.
      +
      * 'if_fast_else_skip' - Only integrity check if the server supplies a hash
      and the local digest computation will run quickly, else skip the check.
      +
      * 'always' - Always check download integrity regardless of possible
      performance costs.
      +
      * 'never' - Don't perform download integrity checks. This setting is
      not recommended except for special cases such as measuring download
      performance excluding time for integrity checking.
      +
      This option exists to assist users who wish to download a composite
      object and are unable to install crcmod with the C-extension. CRC32c is
      the only available integrity check for composite objects, and without the
      C-extension, download performance can be significantly degraded by the
      digest computation. This option is ignored for daisy-chain copies, which
      don't compute hashes but instead (inexpensively) compare the cloud source
      and destination hashes.""")

  DEFAULT_COPY_CHUNK_SIZE = '100Mi'
  DEFAULT_DOWNLOAD_CHUNK_SIZE = '256Ki'
  DEFAULT_UPLOAD_CHUNK_SIZE = '100Mi'
  DEFAULT_MULTIPART_THRESHOLD = '8Mi'
  DEFAULT_MULTIPART_CHUNKSIZE = '8Mi'
  DEFAULT_RESUMABLE_THRESHOLD = '8Mi'
  DEFAULT_BIDI_STREAMING_FLUSH_SIZE = '100Mi'
  DEFAULT_RSYNC_LIST_CHUNK_SIZE = 32000

  def __init__(self):
    super(_SectionStorage, self).__init__('storage')
    self.additional_headers = self._Add(
        'additional_headers',
        help_text=(
            'Includes arbitrary headers in storage API calls.'
            ' Accepts a comma separated list of key=value pairs, e.g.'
            ' `header1=value1,header2=value2`.'
        ),
    )

    self.run_by_gsutil_shim = self._AddBool(
        'run_by_gsutil_shim',
        help_text=(
            'Indicates command was launched by gsutil-to-gcloud-storage shim.'
        ),
        hidden=True,
    )

    self.check_hashes = self._Add(
        'check_hashes',
        default=CheckHashes.IF_FAST_ELSE_FAIL.value,
        help_text=self._CHECK_HASHES_HELP_TEXT,
        choices=([setting.value for setting in CheckHashes]),
    )

    self.enable_server_side_hash_validation = self._AddBool(
        'enable_server_side_hash_validation',
        default=True,
        hidden=False,
        help_text=(
            'If True, hashes will be sent to the server in the last request for'
            ' server-side hash validation during uploads. Client side hash'
            ' validation is still performed for all uploads. For large uploads,'
            ' this may cause a slight performance regression.'
        ),
    )

    self.check_mv_early_deletion_fee = self._AddBool(
        'check_mv_early_deletion_fee',
        default=True,
        help_text=(
            'Block mv commands that may incur an early deletion fee'
            ' (the source object in a mv is deleted).'
        ),
    )

    self.convert_incompatible_windows_path_characters = self._AddBool(
        'convert_incompatible_windows_path_characters',
        default=True,
        help_text=(
            'Allows automatic conversion of invalid path characters on Windows.'
            ' If not enabled, Windows will raise an OSError if an invalid'
            ' character is encountered.'
        ),
    )

    self.copy_chunk_size = self._Add(
        'copy_chunk_size',
        default=self.DEFAULT_COPY_CHUNK_SIZE,
        validator=_HumanReadableByteAmountValidator,
        help_text='Chunk size used for copying to in clouds or on disk.',
    )

    self.download_chunk_size = self._Add(
        'download_chunk_size',
        default=self.DEFAULT_DOWNLOAD_CHUNK_SIZE,
        validator=_HumanReadableByteAmountValidator,
        help_text='Chunk size used for downloading to clouds.',
    )

    self.enable_task_graph_debugging = self._AddBool(
        'enable_task_graph_debugging',
        default=False,
        hidden=True,
        help_text='Enables task graph debugging for gcloud storage commands.',
    )

    self.enable_zonal_buckets_bidi_streaming = self._AddBool(
        'enable_zonal_buckets_bidi_streaming',
        default=True,
        hidden=True,
        help_text=(
            'Enables zonal buckets bidi streaming for gcloud storage commands.'
        ),
    )

    self.use_mrd_bidi_downloads = self._AddBool(
        'use_mrd_bidi_downloads',
        default=True,
        hidden=True,
        help_text=(
            'If True, gcloud storage will use the MRD-based gRPC bidi'
            ' downloads.'
        ),
    )

    self.attempt_grpc_direct_path = self._AddBool(
        'attempt_grpc_direct_path',
        default=True,
        hidden=True,
        help_text=(
            'If True, gRPC will attempt to use DirectPath for Zonal Buckets.'
            'To disable DirectPath, set this property to False.'
        ),
    )

    self.use_nic_isolation = self._AddBool(
        'use_nic_isolation',
        default=False,
        help_text=(
            'If True, gcloud storage sets CPU affinity to isolate 10% of'
            ' CPU cores from network hardware interrupts on machines with > 16'
            ' cores (Linux only). Enable this for high-bandwidth transfers'
            ' (such as with RAPID storage) to reduce CPU contention between'
            ' processes used by gcloud parallelism and network interrupts,'
            ' maximizing throughput.'
        ),
    )

    self.preallocate_disk_space = self._AddBool(
        'preallocate_disk_space',
        default=False,
        hidden=True,
        help_text=(
            'If True, gcloud storage will reserve disk space for bidi '
            'streaming downloads before downloading the data. This can '
            'improve download speeds but may leave empty space if a '
            'download crashes.'
        ),
    )
    self.use_move_object_api = self._AddBool(
        'use_move_object_api',
        default=True,
        hidden=True,
        help_text=(
            'If True, gcloud storage will use the MoveObject API for'
            ' intra-bucket moves when possible.'
        ),
    )

    self.task_graph_debugging_snapshot_duration = self._Add(
        'task_graph_debugging_snapshot_duration',
        default=1,
        hidden=True,
        validator=_IntegerValidator,
        help_text=(
            'The duration in seconds for which the task graph debugging'
            'framework will take a snapshot'
            'of the task graph, task buffer ,'
            'management threads and worker threads'
            'and then display them and provide a'
            'visual representation of the contents'
            'and help track down the issue.'
        ),
    )

    self.upload_chunk_size = self._Add(
        'upload_chunk_size',
        default=self.DEFAULT_UPLOAD_CHUNK_SIZE,
        validator=_HumanReadableByteAmountValidator,
        help_text='Chunk size used for uploading to clouds.',
    )

    self.max_retries = self._Add(
        'max_retries',
        default=23,
        help_text='Max number of retries for operations like copy.',
    )

    self.base_retry_delay = self._Add(
        'base_retry_delay',
        default=1,
        help_text=(
            'Second delay between retrying operations. May be multiplied'
            ' by exponential_sleep_multiplier.'
        ),
    )

    self.exponential_sleep_multiplier = self._Add(
        'exponential_sleep_multiplier',
        default=2,
        help_text='Used in exponential backoff for retrying operations.',
    )

    self.gs_xml_endpoint_url = self._Add(
        'gs_xml_endpoint_url',
        default='https://storage.googleapis.com',
        hidden=True,
        help_text=(
            'The endpoint used to Google Cloud Storage when HMAC '
            'authentication through Boto3.'
        ),
    )

    self.gs_xml_access_key_id = self._Add(
        'gs_xml_access_key_id',
        default=None,
        hidden=True,
        help_text=(
            'Legacy Cloud Storage HMAC credential access key ID.WARNING: This'
            ' in conjunction with storage/gs_xml_secret_access_key forces'
            ' gcloud storage to use the XML API to call Cloud Storage, which'
            ' means not all commands will work as expected.'
        ),
    )

    self.gs_xml_secret_access_key = self._Add(
        'gs_xml_secret_access_key',
        default=None,
        hidden=True,
        help_text=(
            'Legacy Cloud Storage HMAC credential secret access key.'
            'WARNING: This in conjunction with storage/gs_xml_access_key_id '
            'forces gcloud storage to use the XML API to call Cloud Storage, '
            'which means not all commands will work as expected.'
        ),
    )

    self.json_api_version = self._Add(
        'json_api_version',
        default='v1',
        hidden=True,
        help_text=(
            'The version "v1" is hardcoded in the generated client for upload'
            ' operations, e.g.'
            ' /resumable/upload/storage/v1/b/{bucket}/o. Setting this property'
            ' will replace "v1" in the above path with the specified value.'
        ),
    )

    self.key_store_path = self._Add(
        'key_store_path',
        help_text=textwrap.dedent("""\
        Path to a yaml file containing an encryption key, and multiple
        decryption keys for use in storage commands. The file must be formatted
        as follows:
        +
            encryption_key: {A customer-supplied or customer-managed key.}
            decryption_keys:
            - {A customer-supplied key}
            ...
        +
        Customer-supplied encryption keys must be RFC 4648 section 4
        base64-encoded AES256 strings. Customer-managed encryption keys must be
        of the form
        `projects/{project}/locations/{location}/keyRings/{key-ring}/cryptoKeys/{crypto-key}`.
        """),
    )

    self.max_retry_delay = self._Add(
        'max_retry_delay',
        default=32,
        help_text='Max second delay between retriable operations.',
    )

    self.multipart_chunksize = self._Add(
        'multipart_chunksize',
        default=self.DEFAULT_MULTIPART_CHUNKSIZE,
        validator=_HumanReadableByteAmountValidator,
        help_text=(
            'Specifies partition size in bytes of each part of a multipart'
            ' upload made by the Boto3 client. To calculate the maximum size of'
            ' a Boto3 client multipart upload, multiply the multipart_chunk'
            ' value by the maximum number of parts the API allows. For AWS S3'
            ' this limit is 10000. Values can be provided either in bytes or as'
            ' human-readable values (e.g., "150M" to represent 150 mebibytes).'
        ),
    )

    self.multipart_threshold = self._Add(
        'multipart_threshold',
        default=self.DEFAULT_MULTIPART_THRESHOLD,
        validator=_HumanReadableByteAmountValidator,
        help_text=(
            'Files larger than this threshold will be partitioned into parts,'
            ' uploaded separately by the Boto3 client, and then combined into a'
            ' single object. Otherwise, files smaller than this threshold will'
            ' be uploaded by the Boto3 client in a single stream.'
        ),
    )

    self.multiprocessing_default_method = self._Add(
        'multiprocessing_default_method',
        default=None,
        hidden=True,
        help_text=(
            'Specifies the default method to use for multiprocessing in storage'
            ' commands. If not set, the default method is determined by the'
            ' operating system and python version.'
        ),
        choices=['fork', 'spawn', 'forkserver'],
    )

    self.process_count = self._Add(
        'process_count',
        help_text=(
            'The maximum number of processes parallel execution should '
            'use. When process_count and thread_count are both 1, commands use '
            'sequential execution.'
        ),
    )

    self.resumable_threshold = self._Add(
        'resumable_threshold',
        default=self.DEFAULT_RESUMABLE_THRESHOLD,
        validator=_HumanReadableByteAmountValidator,
        help_text=(
            'File operations above this size in bytes will use resumable'
            ' instead of one-shot strategies. For example, a resumable'
            ' download.'
        ),
    )

    self.sliced_object_download_component_size = self._Add(
        'sliced_object_download_component_size',
        validator=_HumanReadableByteAmountValidator,
        help_text=(
            'Target size and upper bound for files to be sliced into.'
            ' Analogous to parallel_composite_upload_component_size.'
        ),
    )

    self.sliced_object_download_max_components = self._Add(
        'sliced_object_download_max_components',
        help_text=(
            'Specifies the maximum number of slices to be used when'
            ' performing a sliced object download. Set None for automatic'
            ' optimization based on system resources.'
        ),
    )

    self.sliced_object_download_threshold = self._Add(
        'sliced_object_download_threshold',
        validator=_HumanReadableByteAmountValidator,
        help_text=(
            'Slice files larger than this value. Zero will block sliced'
            ' downloads. Analogous to parallel_composite_upload_threshold.'
        ),
    )

    self.thread_count = self._Add(
        'thread_count',
        help_text=(
            'The number of threads parallel execution should use per process.'
            ' When process_count and thread_count are both 1, commands use'
            ' sequential execution.'
        ),
    )

    self.parallel_composite_upload_component_prefix = self._Add(
        'parallel_composite_upload_component_prefix',
        default=(
            '/gcloud/tmp/parallel_composite_uploads/'
            'see_gcloud_storage_cp_help_for_details/'
        ),
        help_text=(
            'The prefix used when naming temporary components created by'
            ' composite uploads. If the prefix begins with a `/`, the temporary'
            ' components are uploaded relative to the bucket name. If the'
            ' prefix does not begin with a `/`, the temporary components are'
            ' uploaded relative to the prefix portion of the destination object'
            ' name. For example, consider an upload that will create a final'
            ' object named `gs://bucket/dir1/dir2/object`. Using a prefix of'
            ' `/prefix` means temporary components use names like'
            ' `gs://bucket/prefix/COMPONENT_NAME`. Using a prefix of `prefix`'
            ' means temporary components use names like'
            ' `gs://bucket/dir1/dir2/prefix/COMPONENT_NAME`. Note that this can'
            ' complicate cleaning up temporary components, as they will not all'
            ' share a common prefix. If this property is not specified, gcloud'
            ' storage uses the prefix'
            ' `/gcloud/tmp/parallel_composite_uploads/see_gcloud_storage_cp_help_for_details/`.'
            ' If a chosen prefix results in temporary component names longer'
            ' than the maximum length Cloud Storage allows, gcloud storage'
            ' performs a non-composite upload.'
        ),
    )

    self.parallel_composite_upload_component_size = self._Add(
        'parallel_composite_upload_component_size',
        default='50M',
        validator=_HumanReadableByteAmountValidator,
        help_text=(
            'Specifies the ideal size of a component in bytes, which will act'
            ' as an upper bound to the size of the components if ceil(file_size'
            ' / parallel_composite_upload_component_size) is less than the'
            ' maximum number of objects the API allows composing at once.'
            ' Values can be provided either in bytes or as human-readable'
            ' values (e.g., "150M" to represent 150 mebibytes).'
        ),
    )

    self.parallel_composite_upload_compatibility_check = self._AddBool(
        'parallel_composite_upload_compatibility_check',
        default=True,
        help_text=(
            'Determines if the GET bucket call should be performed to check if'
            ' the default storage class and retention period for the'
            ' destination bucket meet the criteria for parallel composite'
            ' upload.'
        ),
    )

    self.delete_source_objects_in_compose = self._AddBool(
        'delete_source_objects_in_compose',
        default=True,
        hidden=True,
        help_text=(
            'If True, parallel composite uploads will use the delete source '
            'objects feature of the compose API to remove temporary '
            'components, avoiding soft-delete costs. Defaults to True.'
        ),
    )

    self.parallel_composite_upload_enabled = self._Add(
        'parallel_composite_upload_enabled',
        default=None,
        help_text=(
            'Determines whether parallel composite upload should be used.'
            ' Default value is None which will use parallel composite upload'
            ' and log an appropriate warning for the user explaining that'
            ' parallel composite upload is being used by default.'
        ),
        choices=[True, False, None],
    )

    self.parallel_composite_upload_threshold = self._Add(
        'parallel_composite_upload_threshold',
        default='150M',
        validator=_HumanReadableByteAmountValidator,
        help_text=(
            'Specifies the maximum size of a file to upload in a single stream.'
            ' Files larger than this threshold will be partitioned into'
            ' component parts, uploaded in parallel, then composed into a'
            ' single object. The number of components will be the smaller of'
            ' ceil(file_size / parallel_composite_upload_component_size) and'
            ' the maximum number of objects the API allows composing at once.'
            ' For Cloud Storage this limit is 32. This property has no effect'
            ' if parallel_composite_upload_enabled is set to False.'
        ),
    )

    self.bidi_streaming_flush_size = self._Add(
        'bidi_streaming_flush_size',
        default=self.DEFAULT_BIDI_STREAMING_FLUSH_SIZE,
        hidden=True,
        validator=_HumanReadableByteAmountValidator,
        help_text=(
            'The size of the in-memory buffer that is flushed during bidi'
            " streaming uploads. Ensure this is within your machine's RAM"
            ' limits.'
        ),
    )

    self.bidi_streaming_finalize_writes = self._AddBool(
        'bidi_streaming_finalize_writes',
        default=False,
        hidden=True,
        help_text=(
            'If True, the upload will be finalized when the last chunk is'
            ' written. If False, objects will be left in the default'
            ' unfinalized state.'
        ),
    )

    self.rsync_files_directory = self._Add(
        'rsync_files_directory',
        default=PROVIDERS['StorageRsyncFilesDirectory'](),
        help_text='Directory path to intermediary files created by rsync.',
    )

    self.rsync_list_chunk_size = self._Add(
        'rsync_list_chunk_size',
        default=self.DEFAULT_RSYNC_LIST_CHUNK_SIZE,
        help_text=(
            'Number of files processed at a time by the rsync command when'
            ' it builds and compares the list of files at the source'
            ' and destination.'
        ),
    )

    self.use_url_based_rsync_sorting = self._AddBool(
        'use_url_based_rsync_sorting',
        default=False,
        hidden=True,
        help_text=(
            'Enables url based sorting for tracker files used by gcloud storage'
            ' rsync .'
        ),
    )

    self.use_gsutil_rsync_delete_unmatched_destination_objects_behavior = self._AddBool(
        'use_gsutil_rsync_delete_unmatched_destination_objects_behavior',
        default=True,
        help_text=(
            'If True, rsync will preserve unmatched destination objects while'
            ' using --delete-unmatched-destination-objects flag along with'
            ' other flags such as --no-clobber, --skip-unsupported and'
            ' --skip-if-dest-has-newer-mtime just as it would with gsutil.'
        ),
    )

    self.use_rsync_unmatched_gstmp_handling = self._AddBool(
        'use_rsync_unmatched_gstmp_handling',
        default=False,
        hidden=True,
        help_text=(
            'If True, rsync with --delete-unmatched-destination-objects will'
            ' delete unmatched destination gstmp files after the rsync is'
            ' successfully complete. In case of a failed rsync, the unmatched'
            ' destination gstmp files will be deleted only if the customer has'
            ' specified --continue-on-error.'
        ),
    )

    self.s3_endpoint_url = self._Add(
        's3_endpoint_url',
        default=None,
        help_text=(
            'If set, boto3 client will connect to this endpoint. Otherwise,'
            ' boto3 selects a default endpoint based on the AWS service used.'
        ),
    )

    self.suggest_transfer = self._AddBool(
        'suggest_transfer',
        default=True,
        help_text=(
            'If True, logs messages about when Storage Transfer Service'
            ' might be a better tool than gcloud storage.'
        ),
    )

    self.symlink_placeholder_directory = self._Add(
        'symlink_placeholder_directory',
        default=PROVIDERS['StorageSymlinkPlaceholderDirectory'](),
        hidden=True,
        help_text='Directory path to temporary symlink placeholder files.',
    )

    self.tracker_files_directory = self._Add(
        'tracker_files_directory',
        default=PROVIDERS['StorageTrackerFilesDirectory'](),
        help_text='Directory path to tracker files for resumable operations.',
    )

    self.use_gcloud_crc32c = self._AddBool(
        'use_gcloud_crc32c',
        default=None,
        help_text=(
            'If True, data integrity checks use a binary subprocess to '
            ' calculate CRC32C hashes with the included gcloud-crc32c tool'
            ' rather than the google-crc32c Python library. This behavior is '
            ' also triggered when the google-crc32c Python library is'
            ' unavailable even if this property is False.'
        ),
    )

    # TODO(b/109938541): Remove this after implementation seems stable.
    self.use_gsutil = self._AddBool(
        'use_gsutil',
        default=False,
        help_text=(
            'If True, use the deprecated upload implementation which '
            'uses gsutil.'
        ),
    )

    self.use_magicfile = self._AddBool(
        'use_magicfile',
        default=False,
        help_text=(
            'If True, uses the `file --mime <filename>` command to guess'
            ' content types instead of the default filename extension-based'
            ' mechanism. Available on UNIX and macOS (and possibly on Windows, '
            " if you're running Cygwin or some other package that provides "
            ' implementations of UNIX-like commands). When available and '
            ' enabled use_magicfile should be more robust because it analyzes '
            ' file contents in addition to extensions.'
        ),
    )

    self.use_threading_local = self._AddBool(
        'use_threading_local',
        default=True,
        help_text=(
            'If True, reuses some resource if they are already declared on a'
            ' thread. If False, creates duplicates of resources like API'
            ' clients on the same thread. Turning off can help with some bugs'
            ' but will hurt performance.'
        ),
    )

    self.preferred_api = self._Add(
        'preferred_api',
        default=StoragePreferredApi.JSON.value,
        hidden=True,
        help_text=(
            'Specifies the API to be used for performing'
            ' `gcloud storage` operations. If `grpc_with_json_fallback` is set,'
            ' the gRPC API will be used if the operations is supported by'
            ' `gcloud storage`, else it will fallback to using the JSON API.'
        ),
        choices=([api.value for api in StoragePreferredApi]),
    )

    self.use_grpc_if_available = self._AddBool(
        'use_grpc_if_available',
        default=False,
        hidden=True,
        help_text=(
            'If True, uses gRPC when possible. If False, uses existing'
            ' implementation.'
        ),
    )


class CheckHashes(enum.Enum):
  """Different settings for hashing throughout gcloud storage.

  More details in _CHECK_HASHES_HELP_TEXT.
  """

  IF_FAST_ELSE_FAIL = 'if_fast_else_fail'
  IF_FAST_ELSE_SKIP = 'if_fast_else_skip'
  ALWAYS = 'always'
  NEVER = 'never'


class StoragePreferredApi(enum.Enum):
  """Preferred API for gcloud storage."""

  JSON = 'json'
  GRPC_WITH_JSON_FALLBACK = 'grpc_with_json_fallback'

# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import warnings
from datetime import datetime
from cloudsdk.google.protobuf.message import Message
from cloudsdk.google.protobuf.descriptor import FieldDescriptor

# This assumes that the compiled protobuf files (e.g., validation_pb2.py)
# are available in your Python path. You might need to adjust the import
# path based on your project structure.
from orchestration_pipelines_models.pipeline_v1_model.protos import validation_pb2
from orchestration_pipelines_models.utils import time_utils


class PipelineValidator:
    """
    Performs validation on pipeline protobuf messages based on custom field
    options defined in validation.proto.
    """

    @classmethod
    def validate(cls, message: Message):
        """
        Validates a protobuf message.

        This method performs two stages of validation:
        1.  Recursively validates all fields and nested messages against the
            custom validation options defined in the .proto files.
        2.  Performs pipeline-level validation for cross-field consistency,
            such as checking for unique action names and valid dependencies.

        Args:
            message: The protobuf message instance to validate.

        Raises:
            ValueError: If any validation rule is violated.
        """
        cls._validate_message(message, "")

        if message.DESCRIPTOR.full_name == "pipeline_models.OrchestrationPipeline":
            cls._validate_pipeline_level_rules(message)

    @classmethod
    def _validate_message(cls, message: Message, path_prefix: str):
        """Helper method to recursively validate a message."""
        descriptor = message.DESCRIPTOR

        # Do not validate Struct fields, as they can contain arbitrary data that
        # doesn't conform to the validation schema.
        if descriptor.full_name == "google.protobuf.Struct":
            return

        # 1. Loop over all defined fields to check for presence, count, and
        # default-value-based validations. These checks need to run even if
        # the field has its default value (e.g., 0, empty list) and thus
        # wouldn't be in `ListFields()`.
        for field in descriptor.fields:
            current_field_path = (f"{path_prefix}.{field.name}"
                                  if path_prefix else field.name)
            options = field.GetOptions()
            if options.HasExtension(
                    validation_pb2.is_required) and options.Extensions[
                        validation_pb2.is_required]:
                cls._validate_is_required(message, field, current_field_path)

            value = getattr(message, field.name)
            if options.HasExtension(validation_pb2.min_items):
                cls._validate_min_items(
                    field,
                    value,
                    options.Extensions[validation_pb2.min_items],
                    current_field_path,
                )
            if (options.HasExtension(validation_pb2.disallow_zero_enum)
                    and options.Extensions[validation_pb2.disallow_zero_enum]):
                cls._validate_disallow_zero_enum(field, value,
                                                 current_field_path)
            if options.HasExtension(validation_pb2.min_value):
                cls._validate_min_value(
                    field,
                    value,
                    options.Extensions[validation_pb2.min_value],
                    current_field_path,
                )
            if options.HasExtension(validation_pb2.min_len):
                cls._validate_min_len(
                    field,
                    value,
                    options.Extensions[validation_pb2.min_len],
                    current_field_path,
                )

        # 2. Validate the values of all fields that are actually set (non-default).
        for field, value in message.ListFields():
            current_field_path = (f"{path_prefix}.{field.name}"
                                  if path_prefix else field.name)
            cls._validate_field_value(field, value, current_field_path)

            # 3. Recurse into nested messages.
            try:
                is_repeated = (
                    field.cardinality == FieldDescriptor.CARDINALITY_REPEATED)
            except AttributeError:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", DeprecationWarning)
                    is_repeated = field.label == FieldDescriptor.LABEL_REPEATED
            if field.type == FieldDescriptor.TYPE_MESSAGE:
                if is_repeated:
                    # Map fields are represented as repeated message fields.
                    # We need to check if this is a map and if so, skip
                    # recursive validation on its items, as iterating a map
                    # container yields keys (strings), not message objects.
                    if field.message_type.GetOptions().map_entry:
                        continue
                    for i, item in enumerate(value):
                        cls._validate_message(item,
                                              f"{current_field_path}[{i}]")
                else:
                    cls._validate_message(value, current_field_path)

    @classmethod
    def _is_field_repeated(cls, field: FieldDescriptor) -> bool:
        """Checks if a field is repeated, handling different protobuf backends."""
        try:
            return field.cardinality == FieldDescriptor.CARDINALITY_REPEATED
        except AttributeError:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                return field.label == FieldDescriptor.LABEL_REPEATED

    @classmethod
    def _validate_field_value(cls, field: FieldDescriptor, value, path: str):
        """Validates a single field's value based on its options."""
        options = field.GetOptions()

        # Validations for non-default values.
        # Checks for min_items, min_value, min_len and disallow_zero_enum are
        # handled in _validate_message as they need to run on default values.
        if options.HasExtension(validation_pb2.regex):
            cls._validate_regex(field, value,
                                options.Extensions[validation_pb2.regex], path)

        if options.HasExtension(validation_pb2.max_len):
            cls._validate_max_len(field, value,
                                  options.Extensions[validation_pb2.max_len],
                                  path)

        if options.HasExtension(
                validation_pb2.is_cron_expression) and options.Extensions[
                    validation_pb2.is_cron_expression]:
            cls._validate_is_cron_expression(field, value, path)

        if options.HasExtension(
                validation_pb2.is_iso8601_timestamp) and options.Extensions[
                    validation_pb2.is_iso8601_timestamp]:
            cls._validate_is_iso8601_timestamp(field, value, path)

        if options.HasExtension(
                validation_pb2.is_iso8601_duration) and options.Extensions[
                    validation_pb2.is_iso8601_duration]:
            cls._validate_is_iso8601_duration(field, value, path)

        if options.HasExtension(
                validation_pb2.is_iana_timezone) and options.Extensions[
                    validation_pb2.is_iana_timezone]:
            cls._validate_is_iana_timezone(field, value, path)

    @classmethod
    def _validate_is_required(cls, message: Message, field: FieldDescriptor,
                              path: str):
        """Validates that a required field is set."""

        is_repeated = cls._is_field_repeated(field)
        if is_repeated:
            if not getattr(message, field.name):
                raise ValueError(
                    f"Error for field '{path}': field is required and cannot "
                    "be empty.")
        elif field.type == FieldDescriptor.TYPE_MESSAGE:
            if not message.HasField(field.name):
                raise ValueError(
                    f"Error for field '{path}': field is required.")
        elif field.cpp_type == FieldDescriptor.CPPTYPE_STRING:
            if not getattr(message, field.name):
                raise ValueError(
                    f"Error for field '{path}': field is required and cannot "
                    "be an empty string.")

    @classmethod
    def _validate_regex(cls, field: FieldDescriptor, value, pattern: str,
                        path: str):
        """Validates that a string field matches a regex pattern."""
        if field.cpp_type == FieldDescriptor.CPPTYPE_STRING and pattern:
            if not re.match(pattern, value):
                raise ValueError(
                    f"Error for field '{path}': value '{value}' does not match "
                    f"regex pattern '{pattern}'.")

    @classmethod
    def _validate_min_value(cls, field: FieldDescriptor, value, min_val: float,
                            path: str):
        """Validates that a numeric field is above a minimum value."""
        if field.cpp_type in (
                FieldDescriptor.CPPTYPE_INT32,
                FieldDescriptor.CPPTYPE_INT64,
                FieldDescriptor.CPPTYPE_UINT32,
                FieldDescriptor.CPPTYPE_UINT64,
                FieldDescriptor.CPPTYPE_DOUBLE,
                FieldDescriptor.CPPTYPE_FLOAT,
        ):
            if value < min_val:
                raise ValueError(
                    f"Error for field '{path}': value {value} must be at "
                    f"least {min_val}.")

    @classmethod
    def _validate_min_items(cls, field: FieldDescriptor, value, min_i: int,
                            path: str):
        """Validates that a repeated field has a minimum number of items."""
        is_repeated = cls._is_field_repeated(field)
        if is_repeated:
            if len(value) < min_i:
                raise ValueError(
                    f"Error for field '{path}': must have at least {min_i} "
                    f"items, but has {len(value)}.")

    @classmethod
    def _validate_disallow_zero_enum(cls, field: FieldDescriptor, value,
                                     path: str):
        """Validates that an enum field is not its default zero value."""
        if field.type == FieldDescriptor.TYPE_ENUM:
            if value == 0:
                raise ValueError(
                    f"Error for field '{path}': must not be the default enum "
                    "value (0).")

    @classmethod
    def _validate_min_len(cls, field: FieldDescriptor, value, min_l: int,
                          path: str):
        """Validates that a string field has a minimum length."""
        if field.cpp_type == FieldDescriptor.CPPTYPE_STRING:
            if len(value) < min_l:
                raise ValueError(
                    f"Error for field '{path}': length must be at least "
                    f"{min_l}, but is {len(value)}.")

    @classmethod
    def _validate_max_len(cls, field: FieldDescriptor, value, max_l: int,
                          path: str):
        """Validates that a string field has a maximum length."""
        if field.cpp_type == FieldDescriptor.CPPTYPE_STRING:
            if len(value) > max_l:
                raise ValueError(
                    f"Error for field '{path}': length must be at most "
                    f"{max_l}, but is {len(value)}.")

    @classmethod
    def _validate_is_cron_expression(cls, field: FieldDescriptor, value,
                                     path: str):
        """Validates that a string field is a valid cron expression."""
        if field.cpp_type == FieldDescriptor.CPPTYPE_STRING and value:
            try:
                time_utils.check_cron_expression(value)
            except ValueError as e:
                raise ValueError(f"Error for field '{path}': {e}") from e

    @classmethod
    def _validate_is_iso8601_timestamp(cls, field: FieldDescriptor, value,
                                       path: str):
        """Validates that a string field is a valid ISO 8601 timestamp."""
        if field.cpp_type == FieldDescriptor.CPPTYPE_STRING and value:
            try:
                # Replacing 'Z' with '+00:00' for broader Python version
                # compatibility with fromisoformat().
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as e:
                raise ValueError(
                    f"Error for field '{path}': value '{value}' is not a "
                    "valid ISO 8601 timestamp.") from e

    @classmethod
    def _validate_is_iso8601_duration(cls, field: FieldDescriptor, value,
                                      path: str):
        """Validates that a string field is a valid duration string."""
        if field.cpp_type == FieldDescriptor.CPPTYPE_STRING and value:
            try:
                time_utils.check_duration(value)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Error for field '{path}': {e}") from e

    @classmethod
    def _validate_is_iana_timezone(cls, field: FieldDescriptor, value,
                                   path: str):
        """Validates that a string field is a valid IANA timezone."""
        if field.cpp_type == FieldDescriptor.CPPTYPE_STRING and value:
            try:
                time_utils.check_timezone(value)
            except ValueError as e:
                raise ValueError(f"Error for field '{path}': {e}") from e

    @classmethod
    def _validate_pipeline_level_rules(cls, pipeline: Message):
        """Performs pipeline-level validation for action uniqueness and dependencies."""
        if not pipeline.actions:
            return

        action_name_map = {}  # Maps action name to its index in the pipeline.
        all_dependencies = (
            []
        )  # Stores tuples of (dependency_name, action_index, action_type, action_name).

        for i, action_wrapper in enumerate(pipeline.actions):
            action_type = action_wrapper.WhichOneof("action")
            if not action_type:
                continue  # Should not happen in a valid pipeline

            actual_action = getattr(action_wrapper, action_type)
            action_name = actual_action.name

            # 1. Check for unique action names.
            if action_name in action_name_map:
                raise ValueError(
                    f"Error for field 'actions[{i}].{action_type}.name': "
                    f"Duplicate action name '{action_name}' found.")
            action_name_map[action_name] = i

            # Collect all dependencies to check them after all action names are known.
            if hasattr(actual_action, "depends_on"):
                for dep in actual_action.depends_on:
                    all_dependencies.append((dep, i, action_type, action_name))

        # 2. Check for undefined dependencies
        action_names_set = set(action_name_map.keys())
        for dep_name, action_index, action_type, action_name in all_dependencies:
            if dep_name not in action_names_set:
                raise ValueError(
                    f"Error for field 'actions[{action_index}].{action_type}.depends_on': "
                    f"Action '{action_name}' depends on undefined action '{dep_name}'."
                )

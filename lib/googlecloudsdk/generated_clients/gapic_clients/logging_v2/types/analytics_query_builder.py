# -*- coding: utf-8 -*-
# Copyright 2025 Google LLC
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
#
from __future__ import annotations

from typing import MutableMapping, MutableSequence

import proto  # type: ignore

from cloudsdk.google.protobuf import struct_pb2  # type: ignore


__protobuf__ = proto.module(
    package='google.logging.v2',
    manifest={
        'FieldSource',
        'SortOrderParameter',
        'FilterPredicate',
        'ProjectedField',
        'VirtualField',
        'QueryBuilderConfig',
    },
)


class FieldSource(proto.Message):
    r"""A source that can be used to represent a "field of data"
    within various parts of a structured query, such as in SELECT,
    WHERE, or ORDER BY clauses. The term "field of data" is used
    here because it is not limited to literal fields in the
    underlying data schema.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        field (str):
            The fully qualified, dot-delimited path to the selected
            **atomic field** (the leaf value). This path is used for
            primary selection and actions like drill-down or projection.

            The path components should match the exact field names or
            keys as they appear in the underlying data schema. For JSON
            fields, this means respecting the original casing (e.g.,
            ``camelCase`` or ``snake_case`` as present in the JSON).

            To reference field names containing special characters
            (e.g., hyphens, spaces), enclose the individual path segment
            in backticks (\`).

            Examples:

            - ``json_payload.labels.message``
            - ``json_payload.request_id``
            - ``httpRequest.status``
            - ``json_payload.\``\ my-custom-field\`.value\`
            - ``jsonPayload.\``\ my key with spaces\`.data\`

            This field is a member of `oneof`_ ``field_source_type``.
        alias_ref (str):
            The alias name for a field that has already been aliased
            within a different ``ProjectedField`` type elsewhere in the
            query model. The alias must be defined in the
            ``QueryBuilderConfig``'s ``field_sources`` list, otherwise
            the model is invalid.

            This field is a member of `oneof`_ ``field_source_type``.
        projected_field (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ProjectedField):
            A projected field option for when a user
            wants to use a field with some additional
            transformations such as casting or extractions.

            This field is a member of `oneof`_ ``field_source_type``.
        is_json (bool):
            Whether the field is a JSON field, or has a parent that is a
            JSON field. This value is used to determine JSON extractions
            in generated SQL queries. Note that this is_json flag may be
            true when the column_type is not JSON if the parent is a
            JSON field. Ex:

            - A json_payload.message field might have is_json=true,
              since the 'json_payload' parent is of type JSON, and
              columnType='STRING' if the 'message' field is of type
              STRING.
        column_type (str):
            The type of the selected field. This comes
            from the schema. Can be one of the BigQuery data
            types:

              - STRING
              - INT64
              - FLOAT64
              - BOOL
              - TIMESTAMP
              - DATE
              - RECORD
              - JSON
        parent_path (str):
            The dot-delimited path of the **parent container** that
            holds the target field.

            This path defines the structural hierarchy and is essential
            for correctly generating SQL when field keys contain special
            characters (e.g., dots or brackets).

            Example: ``json_payload.labels`` (This points to the
            'labels' object). This is an empty string if the target
            field is at the root level.
    """

    field: str = proto.Field(
        proto.STRING,
        number=1,
        oneof='field_source_type',
    )
    alias_ref: str = proto.Field(
        proto.STRING,
        number=2,
        oneof='field_source_type',
    )
    projected_field: 'ProjectedField' = proto.Field(
        proto.MESSAGE,
        number=5,
        oneof='field_source_type',
        message='ProjectedField',
    )
    is_json: bool = proto.Field(
        proto.BOOL,
        number=6,
    )
    column_type: str = proto.Field(
        proto.STRING,
        number=7,
    )
    parent_path: str = proto.Field(
        proto.STRING,
        number=8,
    )


class SortOrderParameter(proto.Message):
    r"""A sort order for a query based on a column.

    Attributes:
        field_source (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.FieldSource):
            The field to sort on. Can be one of the
            FieldSource types: field name, alias ref,
            variable ref, or a literal value.
        sort_order_direction (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.SortOrderParameter.SortOrder):
            The sort order to use for the query.
    """
    class SortOrder(proto.Enum):
        r"""The sort order types available for the query.

        Values:
            SORT_ORDER_UNSPECIFIED (0):
                Invalid value, do not use.
            SORT_ORDER_NONE (1):
                No sorting will be applied. This is used to
                determine if the query is in pass thru mode.  To
                correctly chart a query in pass thru mode, NONE
                will need to be sent
            SORT_ORDER_ASCENDING (2):
                The lowest-valued entries will be selected.
            SORT_ORDER_DESCENDING (3):
                The highest-valued entries will be selected.
        """
        SORT_ORDER_UNSPECIFIED = 0
        SORT_ORDER_NONE = 1
        SORT_ORDER_ASCENDING = 2
        SORT_ORDER_DESCENDING = 3

    field_source: 'FieldSource' = proto.Field(
        proto.MESSAGE,
        number=3,
        message='FieldSource',
    )
    sort_order_direction: SortOrder = proto.Field(
        proto.ENUM,
        number=2,
        enum=SortOrder,
    )


class FilterPredicate(proto.Message):
    r"""A filter for a query.  This equates to the WHERE clause in
    SQL.

    Attributes:
        operator_type (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.FilterPredicate.OperatorType):
            The operator type for the filter. Currently
            there is no support for multiple levels of
            nesting, so this will be a single value with no
            joining of different operator types
        leaf_predicate (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.FilterPredicate.FilterExpression):
            The leaves of the filter predicate.
            This equates to the last leaves of the filter
            predicate associated with an operator.
        child_predicates (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.FilterPredicate]):
            The children of the filter predicate.
            This equates to the branches of the filter
            predicate that could contain further nested
            leaves.
    """
    class OperatorType(proto.Enum):
        r"""Operator types available for the filter.

        Values:
            OPERATOR_TYPE_UNSPECIFIED (0):
                Invalid value, do not use.
            AND (1):
                AND will be the default operator type.
            OR (2):
                OR operator type.
            LEAF (3):
                LEAF operator type.
        """
        OPERATOR_TYPE_UNSPECIFIED = 0
        AND = 1
        OR = 2
        LEAF = 3

    class FilterExpression(proto.Message):
        r"""This is a leaf of the FilterPredicate. Ex: { field:
        json_payload.message.error_code, filter_value: {numeric_value: 400},
        comparator: EQUAL_TO} The field will be schema field that is
        selected using the . annotation to display the drill down value. The
        value will be the user inputted text that the filter is comparing
        against.

        This message has `oneof`_ fields (mutually exclusive fields).
        For each oneof, at most one member field can be set at the same time.
        Setting any member of the oneof automatically clears all other
        members.

        .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

        Attributes:
            field_source (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.FieldSource):
                Can be one of the FieldSource types: field
                name, alias ref, variable ref, or a literal
                value.
            literal_value (google.protobuf.struct_pb2.Value):
                The Value will be used to hold user defined
                constants set as the Right Hand Side of the
                filter.

                This field is a member of `oneof`_ ``filter_value``.
            field_source_value (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.FieldSource):
                The field. This will be the field that is set
                as the Right Hand Side of the filter.

                This field is a member of `oneof`_ ``filter_value``.
            comparator (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.FilterPredicate.FilterExpression.Comparator):
                The comparison type to use for the filter.
            is_negation (bool):
                Determines if the NOT flag should be added to
                the comparator.
        """
        class Comparator(proto.Enum):
            r"""The filter comparison types.

            Values:
                COMPARATOR_UNSPECIFIED (0):
                    Invalid value, do not use.
                EQUALS (1):
                    The value is equal to the inputted value.
                MATCHES_REGEXP (3):
                    The value is equal to the inputted regex
                    value.
                GREATER_THAN (5):
                    The value is greater than the inputted value.
                LESS_THAN (6):
                    The value is less than the inputted value.
                GREATER_THAN_EQUALS (7):
                    The value is greater than or equal to the
                    inputted value.
                LESS_THAN_EQUALS (8):
                    The value is less than or equal to the
                    inputted value.
                IS_NULL (10):
                    Requires the ``filter_value`` to be a ``Value`` type with
                    ``null_value`` set to true.
                IN (11):
                    The value is in the inputted array value.
                LIKE (12):
                    The value is like the inputted value.
            """
            COMPARATOR_UNSPECIFIED = 0
            EQUALS = 1
            MATCHES_REGEXP = 3
            GREATER_THAN = 5
            LESS_THAN = 6
            GREATER_THAN_EQUALS = 7
            LESS_THAN_EQUALS = 8
            IS_NULL = 10
            IN = 11
            LIKE = 12

        field_source: 'FieldSource' = proto.Field(
            proto.MESSAGE,
            number=9,
            message='FieldSource',
        )
        literal_value: struct_pb2.Value = proto.Field(
            proto.MESSAGE,
            number=7,
            oneof='filter_value',
            message=struct_pb2.Value,
        )
        field_source_value: 'FieldSource' = proto.Field(
            proto.MESSAGE,
            number=8,
            oneof='filter_value',
            message='FieldSource',
        )
        comparator: 'FilterPredicate.FilterExpression.Comparator' = proto.Field(
            proto.ENUM,
            number=5,
            enum='FilterPredicate.FilterExpression.Comparator',
        )
        is_negation: bool = proto.Field(
            proto.BOOL,
            number=6,
        )

    operator_type: OperatorType = proto.Field(
        proto.ENUM,
        number=1,
        enum=OperatorType,
    )
    leaf_predicate: FilterExpression = proto.Field(
        proto.MESSAGE,
        number=3,
        message=FilterExpression,
    )
    child_predicates: MutableSequence['FilterPredicate'] = proto.RepeatedField(
        proto.MESSAGE,
        number=4,
        message='FilterPredicate',
    )


class ProjectedField(proto.Message):
    r"""Represents a field selected in the query, analogous to an item in a
    SQL SELECT clause. It specifies the source field and optionally
    applies transformations like aggregation, casting, regex extraction,
    or assigns an alias. Use ProjectedField when you need more than just
    the raw source field name (for which you might use FieldSource
    directly in QueryBuilderConfig's ``field_sources`` list if no
    transformations or specific operation type are needed).

    A ``ProjectedField`` can represent either a field present in the
    data schema (specified via the ``field`` property) or a
    ``virtual field`` that is computed from other fields (specified via
    the ``virtual_field`` property).

    Attributes:
        field (str):
            Optional. The field name. This will be the
            field that is selected using the dot notation to
            display the drill down value.
        virtual_field (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.VirtualField):
            Optional. A virtual field definition, used in place of
            ``field`` to define a field that is computed from other
            fields rather than being directly present in the data
            schema.

            For example, a virtual field can be defined using
            ``COALESCE`` to select the first non-null value from a list
            of fields.

            If ``virtual_field`` is set, ``field`` must not be set.
        operation (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ProjectedField.FieldOperation):
            Specifies the role of this field (direct
            selection, grouping, or aggregation).
        sql_aggregation_function (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.ProjectedField.FunctionApplication):
            The function to apply to the field.
        alias (str):
            The alias name for the field.
            Valid alias examples are:

              - single word alias: TestAlias
              - numbers in an alias: Alias123
              - multi word alias should be enclosed in
              quotes: "Test Alias" Invalid alias examples
              are:

              - alias containing keywords:  WHERE, SELECT,
              FROM, etc.
              - alias starting with a number: 1stAlias
        cast (str):
            The cast for the field.
            This can any SQL cast type. Examples:

              - STRING
              - CHAR
              - DATE
              - TIMESTAMP
              - DATETIME
              - INT
              - FLOAT
        regex_extraction (str):
            The re2 extraction for the field. This will be used to
            extract the value from the field using REGEXP_EXTRACT. More
            information on re2 can be found here:
            https://github.com/google/re2/wiki/Syntax. Meta characters
            like \*+?()\| will need to be escaped. Examples:

            - ".\ *(autoscaler.*)$" will be converted to
              REGEXP_EXTRACT(JSON_VALUE(field),"request(.\ *(autoscaler.*)$)")\`
              in SQL.
            - "(test_value)$" will be converted to
              REGEXP_EXTRACT(JSON_VALUE(field),"request((test_value)$)")\`
              in SQL.
        truncation_granularity (str):
            The truncation granularity when grouping by a time/date
            field. This will be used to truncate the field to the
            granularity specified. This can be either a date or a time
            granularity found at
            https://cloud.google.com/bigquery/docs/reference/standard-sql/timestamp_functions#timestamp_trunc_granularity_date
            and
            https://cloud.google.com/bigquery/docs/reference/standard-sql/timestamp_functions#timestamp_trunc_granularity_time
            respectively.
    """
    class FieldOperation(proto.Enum):
        r"""Specifies how this field contributes to the query result,
        particularly regarding grouping and aggregation.

        Values:
            FIELD_OPERATION_UNSPECIFIED (0):
                Invalid value. Operation must be specified.
            NO_SETTING (1):
                Select the field directly without grouping or
                aggregation. Corresponds to including the raw
                field (potentially with cast, regex, or alias)
                in the SELECT list.
            GROUP_BY (2):
                Group the query results by the distinct
                values of this field. Corresponds to including
                the field (potentially truncated) in the GROUP
                BY clause.
            AGGREGATE (3):
                Apply an aggregation function to this field across grouped
                results. Corresponds to applying a function like COUNT, SUM,
                AVG in the SELECT list. Requires
                ``sql_aggregation_function`` to be set.
        """
        FIELD_OPERATION_UNSPECIFIED = 0
        NO_SETTING = 1
        GROUP_BY = 2
        AGGREGATE = 3

    class FunctionApplication(proto.Message):
        r"""Defines the aggregation function to apply to this field. This
        message is used only when ``operation`` is set to ``AGGREGATE``.

        Attributes:
            type_ (str):
                Required. Specifies the aggregation function. Use one of the
                following string identifiers: "average": Computes the
                average (AVG). Applies only to numeric values. "count":
                Counts the number of values (COUNT). "count-distinct":
                Counts the number of distinct values (COUNT DISTINCT).
                "count-distinct-approx": Approximates the count of distinct
                values (APPROX_COUNT_DISTINCT). "max": Finds the maximum
                value (MAX). Applies only to numeric values. "min": Finds
                the minimum value (MIN). Applies only to numeric values.
                "sum": Computes the sum (SUM). Applies only to numeric
                values.
            parameters (MutableSequence[google.protobuf.struct_pb2.Value]):
                Optional. Parameters to be applied to the
                aggregation. Aggregations that support or
                require parameters are listed above.
        """

        type_: str = proto.Field(
            proto.STRING,
            number=1,
        )
        parameters: MutableSequence[struct_pb2.Value] = proto.RepeatedField(
            proto.MESSAGE,
            number=2,
            message=struct_pb2.Value,
        )

    field: str = proto.Field(
        proto.STRING,
        number=1,
    )
    virtual_field: 'VirtualField' = proto.Field(
        proto.MESSAGE,
        number=9,
        message='VirtualField',
    )
    operation: FieldOperation = proto.Field(
        proto.ENUM,
        number=2,
        enum=FieldOperation,
    )
    sql_aggregation_function: FunctionApplication = proto.Field(
        proto.MESSAGE,
        number=8,
        message=FunctionApplication,
    )
    alias: str = proto.Field(
        proto.STRING,
        number=4,
    )
    cast: str = proto.Field(
        proto.STRING,
        number=5,
    )
    regex_extraction: str = proto.Field(
        proto.STRING,
        number=6,
    )
    truncation_granularity: str = proto.Field(
        proto.STRING,
        number=7,
    )


class VirtualField(proto.Message):
    r"""A virtual field is a field that is not physically present in
    the underlying data schema, but is created through specific
    operations within the query builder model based on other fields
    in the schema.

    Attributes:
        virtual_field_type (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.VirtualField.VirtualFieldType):
            Required. The type of the virtual field.
        underlying_field_sources (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.FieldSource]):
            The field sources that will be used to create the virtual
            field, based on the semantics of the virtual field type.

            The field sources must follow these rules, based on the
            virtual field type:

            - For VIRTUAL_FIELD_TYPE_UNSPECIFIED, this field must be
              empty.
            - For COALESCE, this field must be non-empty and include a
              minimum of two field sources. The underlying field sources
              must be actual projected fields that represent actual
              schema fields and that must not be transformed and
              aggregated in any way, except for casting. The type of all
              the underlying field sources must be equivalent so that
              picking one of them would result in the same value type.
    """
    class VirtualFieldType(proto.Enum):
        r"""The type options of the virtual field.

        Values:
            VIRTUAL_FIELD_TYPE_UNSPECIFIED (0):
                Invalid value, do not use.
            COALESCE (1):
                Creates a virtual field by selecting the first non-null
                value from the list of fields specified in
                ``underlying_field_sources``, similar to a COALESCE function
                in SQL.
        """
        VIRTUAL_FIELD_TYPE_UNSPECIFIED = 0
        COALESCE = 1

    virtual_field_type: VirtualFieldType = proto.Field(
        proto.ENUM,
        number=1,
        enum=VirtualFieldType,
    )
    underlying_field_sources: MutableSequence['FieldSource'] = proto.RepeatedField(
        proto.MESSAGE,
        number=2,
        message='FieldSource',
    )


class QueryBuilderConfig(proto.Message):
    r"""Defines a structured query configuration that can be used
    instead of writing raw SQL. This configuration represents the
    components of a SQL query (FROM, SELECT, WHERE, ORDER BY, LIMIT)
    and is typically converted into an executable query (e.g.,
    BigQuery SQL) by the backend service to retrieve data for
    analysis or visualization.

    Attributes:
        resource_names (MutableSequence[str]):
            Required. The view/resource to query. For now only a single
            view/resource will be sent, but there are plans to allow
            multiple views in the future. Marking as repeated for that
            purpose. Example:

            - "projects/123/locations/global/buckets/456/views/\_Default"
            - "projects/123/locations/global/metricBuckets/456/views/\_Default".
        filter (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.FilterPredicate):
            The filter to use for the query. This equates
            to the WHERE clause in SQL.
        field_sources (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.FieldSource]):
            Defines the items to include in the query
            result, analogous to a SQL SELECT clause.
        limit (int):
            The limit to use for the query. This equates
            to the LIMIT clause in SQL. A limit of 0 will be
            treated as not enabled.
        order_bys (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.SortOrderParameter]):
            The sort orders to use for the query. This
            equates to the ORDER BY clause in SQL.
        search_term (str):
            The plain text search to use for the query. There is no
            support for multiple search terms. This uses the ``SEARCH``
            functionality in BigQuery. For example, a
            ``search_term = 'ERROR'`` would result in the following SQL:

            SELECT \* FROM ``resource`` WHERE SEARCH(``resource``,
            'ERROR') LIMIT 100
    """

    resource_names: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=1,
    )
    filter: 'FilterPredicate' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='FilterPredicate',
    )
    field_sources: MutableSequence['FieldSource'] = proto.RepeatedField(
        proto.MESSAGE,
        number=7,
        message='FieldSource',
    )
    limit: int = proto.Field(
        proto.INT64,
        number=4,
    )
    order_bys: MutableSequence['SortOrderParameter'] = proto.RepeatedField(
        proto.MESSAGE,
        number=5,
        message='SortOrderParameter',
    )
    search_term: str = proto.Field(
        proto.STRING,
        number=6,
    )


__all__ = tuple(sorted(__protobuf__.manifest))

# Copyright 2018-2019 Faculty Science Limited
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

from collections import namedtuple
from enum import Enum
import uuid

from marshmallow import fields, post_load, utils as marshmallow_utils
from marshmallow_enum import EnumField

from faculty.clients.base import BaseClient, BaseSchema, Conflict


class ExperimentNameConflict(Exception):
    def __init__(self, name):
        tpl = "An experiment with name '{}' already exists in that project"
        message = tpl.format(name)
        super(ExperimentNameConflict, self).__init__(message)


class ParamConflict(Exception):
    def __init__(self, message, conflicting_params=None):
        super(ParamConflict, self).__init__(message)
        if conflicting_params is None:
            self.conflicting_params = []
        else:
            self.conflicting_params = conflicting_params


class ExperimentDeleted(Exception):
    def __init__(self, message, experiment_id):
        super(ExperimentDeleted, self).__init__(message)
        self.experiment_id = experiment_id


class RunQueryFilterValidation(Exception):
    def __init__(self, message, value):
        super(RunQueryFilterValidation, self).__init__(message)
        self.value = value


class ExperimentRunStatus(Enum):
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    SCHEDULED = "scheduled"


Experiment = namedtuple(
    "Experiment",
    [
        "id",
        "name",
        "description",
        "artifact_location",
        "created_at",
        "last_updated_at",
        "deleted_at",
    ],
)


ExperimentRun = namedtuple(
    "ExperimentRun",
    [
        "id",
        "run_number",
        "experiment_id",
        "name",
        "parent_run_id",
        "artifact_location",
        "status",
        "started_at",
        "ended_at",
        "deleted_at",
        "tags",
        "params",
        "metrics",
    ],
)

Metric = namedtuple("Metric", ["key", "value", "timestamp"])
Param = namedtuple("Param", ["key", "value"])
Tag = namedtuple("Tag", ["key", "value"])

Page = namedtuple("Page", ["start", "limit"])
Pagination = namedtuple("Pagination", ["start", "size", "previous", "next"])
ListExperimentRunsResponse = namedtuple(
    "ListExperimentRunsResponse", ["runs", "pagination"]
)
DeleteExperimentRunsResponse = namedtuple(
    "DeleteExperimentRunsResponse", ["deleted_run_ids", "conflicted_run_ids"]
)
RestoreExperimentRunsResponse = namedtuple(
    "RestoreExperimentRunsResponse", ["restored_run_ids", "conflicted_run_ids"]
)

_SingleFilter = namedtuple("_SingleFilter", ["by", "key", "operator", "value"])


class SingleFilter(_SingleFilter):
    def __new__(cls, by, key, operator, value):
        if by.needs_key() and key is None:
            raise ValueError(
                "key must not be none for filter type {}".format(by)
            )
        elif not by.needs_key() and key is not None:
            raise ValueError("key must be none for filter type {}".format(by))
        return super(SingleFilter, cls).__new__(cls, by, key, operator, value)


CompoundFilter = namedtuple("CompoundFilter", ["operator", "conditions"])


class SingleFilterOperator(Enum):
    DEFINED = "defined"
    EQUAL_TO = "eq"
    NOT_EQUAL_TO = "ne"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL_TO = "le"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL_TO = "ge"


class SingleFilterBy(Enum):
    PROJECT_ID = "projectId"
    EXPERIMENT_ID = "experimentId"
    RUN_ID = "runId"
    DELETED_AT = "deletedAt"
    TAG = "tag"
    PARAM = "param"
    METRIC = "metric"

    def needs_key(self):
        return self in {
            SingleFilterBy.TAG,
            SingleFilterBy.PARAM,
            SingleFilterBy.METRIC,
        }


class CompoundFilterOperator(Enum):
    AND = "and"
    OR = "or"


_Sort = namedtuple("_Sort", ["by", "key", "order"])


class Sort(_Sort):
    def __new__(cls, by, key, order):
        if by.needs_key() and key is None:
            raise ValueError(
                "key must not be none for sort type {}".format(by)
            )
        elif not by.needs_key() and key is not None:
            raise ValueError("key must be none for sort type {}".format(by))
        return super(Sort, cls).__new__(cls, by, key, order)


class SortBy(Enum):
    STARTED_AT = "startedAt"
    RUN_NUMBER = "runNumber"
    DURATION = "duration"
    TAG = "tag"
    PARAM = "param"
    METRIC = "metric"

    def needs_key(self):
        return self in {SortBy.TAG, SortBy.PARAM, SortBy.METRIC}


class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"


QueryRuns = namedtuple("QueryRuns", ["filter", "sort", "page"])


class PageSchema(BaseSchema):
    start = fields.Integer(required=True)
    limit = fields.Integer(required=True)

    @post_load
    def make_page(self, data):
        return Page(**data)


class MetricSchema(BaseSchema):
    key = fields.String(required=True)
    value = fields.Float(required=True)
    timestamp = fields.DateTime(required=True)

    @post_load
    def make_metric(self, data):
        return Metric(**data)


class ParamSchema(BaseSchema):
    key = fields.String(required=True)
    value = fields.String(required=True)

    @post_load
    def make_param(self, data):
        return Param(**data)


class TagSchema(BaseSchema):
    key = fields.String(required=True)
    value = fields.String(required=True)

    @post_load
    def make_tag(self, data):
        return Tag(**data)


class LifecycleStage(Enum):
    ACTIVE = "active"
    DELETED = "deleted"


class ExperimentSchema(BaseSchema):
    id = fields.Integer(data_key="experimentId", required=True)
    name = fields.String(required=True)
    description = fields.String(required=True)
    artifact_location = fields.String(
        data_key="artifactLocation", required=True
    )
    created_at = fields.DateTime(data_key="createdAt", required=True)
    last_updated_at = fields.DateTime(data_key="lastUpdatedAt", required=True)
    deleted_at = fields.DateTime(data_key="deletedAt", missing=None)

    @post_load
    def make_experiment(self, data):
        return Experiment(**data)


class ExperimentRunSchema(BaseSchema):
    id = fields.UUID(data_key="runId", required=True)
    run_number = fields.Integer(data_key="runNumber", required=True)
    experiment_id = fields.Integer(data_key="experimentId", required=True)
    name = fields.String(required=True)
    parent_run_id = fields.UUID(data_key="parentRunId", missing=None)
    artifact_location = fields.String(
        data_key="artifactLocation", required=True
    )
    status = EnumField(ExperimentRunStatus, by_value=True, required=True)
    started_at = fields.DateTime(data_key="startedAt", required=True)
    ended_at = fields.DateTime(data_key="endedAt", missing=None)
    deleted_at = fields.DateTime(data_key="deletedAt", missing=None)
    tags = fields.Nested(TagSchema, many=True, required=True)
    params = fields.Nested(ParamSchema, many=True, required=True)
    metrics = fields.Nested(MetricSchema, many=True, required=True)

    @post_load
    def make_experiment_run(self, data):
        return ExperimentRun(**data)


class ExperimentRunDataSchema(BaseSchema):
    metrics = fields.List(fields.Nested(MetricSchema))
    params = fields.List(fields.Nested(ParamSchema))
    tags = fields.List(fields.Nested(TagSchema))


class ExperimentRunInfoSchema(BaseSchema):
    status = EnumField(ExperimentRunStatus, by_value=True, required=True)
    ended_at = fields.DateTime(data_key="endedAt", missing=None)


class PaginationSchema(BaseSchema):
    start = fields.Integer(required=True)
    size = fields.Integer(required=True)
    previous = fields.Nested(PageSchema, missing=None)
    next = fields.Nested(PageSchema, missing=None)

    @post_load
    def make_pagination(self, data):
        return Pagination(**data)


class ListExperimentRunsResponseSchema(BaseSchema):
    pagination = fields.Nested(PaginationSchema, required=True)
    runs = fields.Nested(ExperimentRunSchema, many=True, required=True)

    @post_load
    def make_list_runs_response_schema(self, data):
        return ListExperimentRunsResponse(**data)


class CreateRunSchema(BaseSchema):
    name = fields.String()
    parent_run_id = fields.UUID(data_key="parentRunId")
    started_at = fields.DateTime(data_key="startedAt")
    artifact_location = fields.String(data_key="artifactLocation")
    tags = fields.Nested(TagSchema, many=True, required=True)


class DeleteExperimentRunsResponseSchema(BaseSchema):
    deleted_run_ids = fields.List(
        fields.UUID(), data_key="deletedRunIds", required=True
    )
    conflicted_run_ids = fields.List(
        fields.UUID(), data_key="conflictedRunIds", required=True
    )

    @post_load
    def make_delete_runs_response(self, data):
        return DeleteExperimentRunsResponse(**data)


class RestoreExperimentRunsResponseSchema(BaseSchema):
    restored_run_ids = fields.List(
        fields.UUID(), data_key="restoredRunIds", required=True
    )
    conflicted_run_ids = fields.List(
        fields.UUID(), data_key="conflictedRunIds", required=True
    )

    @post_load
    def make_restore_runs_response(self, data):
        return RestoreExperimentRunsResponse(**data)


class SingleFilterValueField(fields.Field):
    """
    Field that serialises/deserialises a run filter.
    """

    def _is_valid_uuid(self, value, obj):
        return isinstance(value, uuid.UUID) and (
            obj.by in {SingleFilterBy.PROJECT_ID, SingleFilterBy.RUN_ID}
        )

    def _is_valid_experiment_id(self, value, obj):
        return (
            isinstance(value, int) and obj.by == SingleFilterBy.EXPERIMENT_ID
        )

    def _is_directly_stringifiable(self, value, obj):
        return (
            self._is_valid_uuid(value, obj)
            or self._is_valid_experiment_id(value, obj)
            or obj.by
            in {
                SingleFilterBy.TAG,
                SingleFilterBy.PARAM,
                SingleFilterBy.METRIC,
            }
        )

    def _deserialize(self, value, attr, data, **kwargs):
        return value

    def _serialize(self, value, attr, obj, **kwargs):
        if self._is_directly_stringifiable(value, obj):
            return str(value)
        elif obj.by == SingleFilterBy.DELETED_AT:
            return marshmallow_utils.from_iso_datetime(str(value)).isoformat()
        else:
            raise RunQueryFilterValidation(
                "Validation error serialising run query filter", value
            )


class FilterField(fields.Field):
    """
    Field that serialises/deserialises a run filter.
    """

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None
        elif isinstance(value, SingleFilter):
            return SingleFilterSchema().load(value)
        else:
            return CompoundFilterSchema().load(value)

    def _serialize(self, value, attr, obj, **kwargs):
        print(type(obj))
        if value is None and isinstance(obj, QueryRuns):
            return None
        elif value is None:
            raise RunQueryFilterValidation(
                "Validation error serialising a None filter", value
            )
        if isinstance(value, SingleFilter):
            return SingleFilterSchema().dump(value)
        else:
            return CompoundFilterSchema().dump(value)


class SingleFilterSchema(BaseSchema):
    by = EnumField(SingleFilterBy, by_value=True, required=True)
    key = fields.String()
    operator = EnumField(SingleFilterOperator, by_value=True, required=True)
    value = SingleFilterValueField(required=True)


class CompoundFilterSchema(BaseSchema):
    operator = EnumField(CompoundFilterOperator, by_value=True, required=True)
    conditions = fields.List(FilterField(skip_if=None))


class SortSchema(BaseSchema):
    by = EnumField(SortBy, by_value=True, required=True)
    key = fields.String()
    order = EnumField(SortOrder, by_value=True, required=True)


class QueryRunsSchema(BaseSchema):
    filter = FilterField(required=True)
    sort = fields.List(fields.Nested(SortSchema))
    page = fields.Nested(PageSchema, missing=None)


class MetricHistorySchema(BaseSchema):
    history = fields.Nested(MetricSchema, many=True, required=True)

    @post_load
    def extract_history(self, data):
        return data["history"]


class ExperimentClient(BaseClient):

    SERVICE_NAME = "atlas"

    def create(
        self, project_id, name, description=None, artifact_location=None
    ):
        """Create an experiment.

        Parameters
        ----------
        project_id : uuid.UUID
        name : str
        description : str, optional
        artifact_location : str, optional

        Returns
        -------
        Experiment

        Raises
        ------
        ExperimentNameConflict
            When an experiment of the provided name already exists in the
            project.
        """
        endpoint = "/project/{}/experiment".format(project_id)
        payload = {
            "name": name,
            "description": description,
            "artifactLocation": artifact_location,
        }
        try:
            return self._post(endpoint, ExperimentSchema(), json=payload)
        except Conflict as err:
            if err.error_code == "experiment_name_conflict":
                raise ExperimentNameConflict(name)
            else:
                raise

    def get(self, project_id, experiment_id):
        """Get a specified experiment.

        Parameters
        ----------
        project_id : uuid.UUID
        experiment_id : int

        Returns
        -------
        Experiment
        """
        endpoint = "/project/{}/experiment/{}".format(
            project_id, experiment_id
        )
        return self._get(endpoint, ExperimentSchema())

    def list(self, project_id, lifecycle_stage=None):
        """List the experiments in a project.

        Parameters
        ----------
        project_id : uuid.UUID
        lifecycle_stage : LifecycleStage, optional
            To filter experiments in the given lifecycle stage only
            (ACTIVE | DELETED). By default, all experiments in the
            project are returned.

        Returns
        -------
        List[Experiment]
        """
        query_params = {}
        if lifecycle_stage is not None:
            query_params["lifecycleStage"] = lifecycle_stage.value
        endpoint = "/project/{}/experiment".format(project_id)
        return self._get(
            endpoint, ExperimentSchema(many=True), params=query_params
        )

    def update(self, project_id, experiment_id, name=None, description=None):
        """Update the name and/or description of an experiment.

        Parameters
        ----------
        project_id : uuid.UUID
        experiment_id : int
        name : str, optional
            The new name of the experiment. If not provided, the name will not
            be modified.
        description : str, optional
            The new description of the experiment. If not provided, the
            description will not be modified.

        Raises
        ------
        ExperimentNameConflict
            When an experiment of the provided name already exists in the
            project.
        """
        endpoint = "/project/{}/experiment/{}".format(
            project_id, experiment_id
        )
        payload = {"name": name, "description": description}
        try:
            self._patch_raw(endpoint, json=payload)
        except Conflict as err:
            if err.error_code == "experiment_name_conflict":
                raise ExperimentNameConflict(name)
            else:
                raise

    def delete(self, project_id, experiment_id):
        """Delete a specified experiment.

        Parameters
        ----------
        project_id : uuid.UUID
        experiment_id : int
        """
        endpoint = "/project/{}/experiment/{}".format(
            project_id, experiment_id
        )
        self._delete_raw(endpoint)

    def restore(self, project_id, experiment_id):
        """Restore a specified experiment.

        Parameters
        ----------
        project_id : uuid.UUID
        experiment_id : int
        """
        endpoint = "/project/{}/experiment/{}/restore".format(
            project_id, experiment_id
        )
        self._put_raw(endpoint)

    def create_run(
        self,
        project_id,
        experiment_id,
        name,
        started_at,
        parent_run_id=None,
        artifact_location=None,
        tags=None,
    ):
        """Create a run in a project.

        Parameters
        ----------
        project_id : uuid.UUID
        experiment_id : int
        name : str
        started_at : datetime.datetime
            Time at which the run was started. If the datetime does not have a
            timezone, it will be assumed to be in UTC.
        parent_run_id : uuid.UUID, optional
            The ID of the parent run, if any.
        artifact_location: str, optional
            The location of the artifact repository to use for this run.
            If omitted, the value of `artifact_location` for the experiment
            will be used.
        tags: List[Tag]

        Returns
        -------
        ExperimentRun

        Raises
        ------
        ExperimentDeleted
            When the run that is being updated refers to an experiment that is
            deleted
        """
        if tags is None:
            tags = []

        endpoint = "/project/{}/experiment/{}/run".format(
            project_id, experiment_id
        )
        payload = CreateRunSchema().dump(
            {
                "name": name,
                "parent_run_id": parent_run_id,
                "started_at": started_at,
                "artifact_location": artifact_location,
                "tags": tags,
            }
        )
        try:
            return self._post(endpoint, ExperimentRunSchema(), json=payload)
        except Conflict as err:
            if err.error_code == "experiment_deleted":
                raise ExperimentDeleted(
                    err.error, err.response.json()["experimentId"]
                )
            else:
                raise

    def get_run(self, project_id, run_id):
        """Get a specified experiment run.

        Parameters
        ----------
        project_id : uuid.UUID
        run_id : uuid.UUID

        Returns
        -------
        ExperimentRun
        """
        endpoint = "/project/{}/run/{}".format(project_id, run_id)
        return self._get(endpoint, ExperimentRunSchema())

    def list_runs(
        self,
        project_id,
        experiment_ids=None,
        lifecycle_stage=None,
        start=None,
        limit=None,
    ):
        """List experiment runs.

        This method returns pages of runs. If less than the full number of runs
        for the job is returned, the ``next`` page of the returned response
        object will not be ``None``:

        >>> response = client.list_runs(project_id)
        >>> response.pagination.next
        Page(start=10, limit=10)

        Get all experiment runs by making successive calls to ``list_runs``,
        passing the ``start`` and ``limit`` of the ``next`` page each time
        until ``next`` is returned as ``None``.

        Parameters
        ----------
        project_id : uuid.UUID
        experiment_ids : List[int], optional
            To filter runs of experiments with the given IDs only. If an empty
            list is passed, a result with an empty list of runs is returned.
            By default, runs from all experiments are returned.
        start : int, optional
            The (zero-indexed) starting point of runs to retrieve.
        limit : int, optional
            The maximum number of runs to retrieve.

        Returns
        -------
        ListExperimentRunsResponse
        """
        if lifecycle_stage is not None:
            raise NotImplementedError("lifecycle_stage is not supported.")

        query_params = []
        if experiment_ids is not None:
            if len(experiment_ids) == 0:
                return ListExperimentRunsResponse(
                    runs=[],
                    pagination=Pagination(
                        start=0, size=0, previous=None, next=None
                    ),
                )
            for experiment_id in experiment_ids:
                query_params.append(("experimentId", experiment_id))

        if start is not None:
            query_params.append(("start", start))
        if limit is not None:
            query_params.append(("limit", limit))

        endpoint = "/project/{}/run".format(project_id)
        return self._get(
            endpoint, ListExperimentRunsResponseSchema(), params=query_params
        )

    def query_runs(
        self, project_id, filter=None, sort=None, start=None, limit=None
    ):
        """Query experiment runs.

        This method returns pages of runs. If less than the full number of runs
        for the job is returned, the ``next`` page of the returned response
        object will not be ``None``:

        >>> response = client.query_runs(project_id)
        >>> response.pagination.next
        Page(start=10, limit=10)

        Get all experiment runs by making successive calls to ``query_runs``,
        passing the ``start`` and ``limit`` of the ``next`` page each time
        until ``next`` is returned as ``None``.

        Parameters
        ----------
        project_id : uuid.UUID
        filter: either SingleFilter object or CompoundFilter object, optional
            To filter runs of experiments with the given filter. By default,
            runs from all experiments are returned.
        sort: List[Sort], optional
            Runs are ordered using sorting elements lexicographically. By
            default, experiment runs are sorted by their startedAt value.
        start : int, optional
            The (zero-indexed) starting point of runs to retrieve.
        limit : int, optional
            The maximum number of runs to retrieve.

        Returns
        -------
        ListExperimentRunsResponse
        """
        endpoint = "/project/{}/run/query".format(project_id)
        page = None
        if start is not None and limit is not None:
            page = Page(start, limit)
        payload = QueryRunsSchema().dump(QueryRuns(filter, sort, page))
        return self._post(
            endpoint, ListExperimentRunsResponseSchema(), json=payload
        )

    def log_run_data(
        self, project_id, run_id, metrics=None, params=None, tags=None
    ):
        """Update the data of a run.

        Parameters
        ----------
        project_id : uuid.UUID
        run_id : uuid.UUID
        metrics : List[Metric], optional
            Each metric will be inserted.
        params : List[Param], optional
            Each param will be inserted. Note that on a name conflict the
            entire operation will be rejected.
        tags : List[Tag], optional
            Each tag be upserted.

        Raises
        ------
        ParamConflict
            When a provided param already exists and has a different value than
            was specified.
        """
        if all(kwarg is None for kwarg in [metrics, params, tags]):
            return
        endpoint = "/project/{}/run/{}/data".format(project_id, run_id)
        payload = ExperimentRunDataSchema().dump(
            {"metrics": metrics, "params": params, "tags": tags}
        )
        try:
            self._patch_raw(endpoint, json=payload)
        except Conflict as err:
            if err.error_code == "conflicting_params":
                raise ParamConflict(
                    err.error, err.response.json()["parameterKeys"]
                )
            else:
                raise

    def update_run_info(self, project_id, run_id, status=None, ended_at=None):
        """Update the status and end time of a run.

        Parameters
        ----------
        project_id : uuid.UUID
        run_id : uuid.UUID
        status: ExperimentRunStatus, optional
        ended_at: datetime, optional

        Returns
        -------
        ExperimentRun
        """
        endpoint = "/project/{}/run/{}/info".format(project_id, run_id)
        payload = ExperimentRunInfoSchema().dump(
            {"status": status, "ended_at": ended_at}
        )
        return self._patch(endpoint, ExperimentRunSchema(), json=payload)

    def get_metric_history(self, project_id, run_id, key):
        """Get the history of a metric.

        Parameters
        ----------
        project_id : uuid.UUID
        run_id : uuid.UUID
        key: string

        Returns
        -------
        List[Metric], ordered by timestamp and value
        """
        endpoint = "/project/{}/run/{}/metric/{}/history".format(
            project_id, run_id, key
        )
        return self._get(endpoint, MetricHistorySchema())

    def delete_runs(self, project_id, run_ids=None):
        """Delete experiment runs.

        Parameters
        ----------
        project_id : uuid.UUID
        run_ids : List[uuid.UUID], optional
            A list of run IDs to delete. If not specified, all runs in the
            project will be deleted. If an empty list is passed, no runs
            will be deleted.

        Returns
        -------
        DeleteExperimentRunsResponse
            Containing lists of successfully deleted and conflicting (already
            deleted) run IDs.
        """
        endpoint = "/project/{}/run/delete/query".format(project_id)

        if run_ids is None:
            # Delete all runs in project
            payload = {}  # No filter
        elif len(run_ids) == 0:
            return DeleteExperimentRunsResponse(
                deleted_run_ids=[], conflicted_run_ids=[]
            )
        else:
            payload = {
                "filter": {
                    "operator": "or",
                    "conditions": [
                        {"by": "runId", "operator": "eq", "value": str(run_id)}
                        for run_id in run_ids
                    ],
                }
            }

        return self._post(
            endpoint, DeleteExperimentRunsResponseSchema(), json=payload
        )

    def restore_runs(self, project_id, run_ids=None):
        """Restore experiment runs.

        Parameters
        ----------
        project_id : uuid.UUID
        run_ids : List[uuid.UUID], optional
            A list of run IDs to restore. If not specified, all runs in the
            project will be restored. If an empty list is passed, no runs
            will be restored.

        Returns
        -------
        RestoreExperimentRunsResponse
            Containing lists of successfully restored and conflicting (already
            active) run IDs.
        """
        endpoint = "/project/{}/run/restore/query".format(project_id)

        if run_ids is None:
            # Restore all runs in project
            payload = {}  # No filter
        elif len(run_ids) == 0:
            return RestoreExperimentRunsResponse(
                restored_run_ids=[], conflicted_run_ids=[]
            )
        else:
            payload = {
                "filter": {
                    "operator": "or",
                    "conditions": [
                        {"by": "runId", "operator": "eq", "value": str(run_id)}
                        for run_id in run_ids
                    ],
                }
            }

        return self._post(
            endpoint, RestoreExperimentRunsResponseSchema(), json=payload
        )

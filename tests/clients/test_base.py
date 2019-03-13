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

import pytest
from faculty.clients.base import (
    BadGateway,
    BadRequest,
    BaseClient,
    BaseSchema,
    Conflict,
    Forbidden,
    GatewayTimeout,
    HttpError,
    InternalServerError,
    InvalidResponse,
    MethodNotAllowed,
    NotFound,
    ServiceUnavailable,
    Unauthorized,
)
from marshmallow import fields, post_load

MOCK_SERVICE_NAME = "test-service"
MOCK_ENDPOINT = "/endpoint"
MOCK_SERVICE_URL = "https://test-service.example.com/endpoint"

AUTHORIZATION_HEADER_VALUE = "Bearer mock-token"
AUTHORIZATION_HEADER = {"Authorization": AUTHORIZATION_HEADER_VALUE}

BAD_RESPONSE_STATUSES = [
    (400, BadRequest),
    (401, Unauthorized),
    (403, Forbidden),
    (404, NotFound),
    (405, MethodNotAllowed),
    (409, Conflict),
    (500, InternalServerError),
    (502, BadGateway),
    (503, ServiceUnavailable),
    (504, GatewayTimeout),
    (418, HttpError),
]

HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]


@pytest.fixture
def session(mocker):
    session = mocker.Mock()
    session.service_url.return_value = MOCK_SERVICE_URL

    yield session

    session.service_url.assert_called_once_with(
        MOCK_SERVICE_NAME, MOCK_ENDPOINT
    )


@pytest.fixture
def patch_auth(mocker, session):
    def _add_auth_headers(request):
        request.headers["Authorization"] = AUTHORIZATION_HEADER_VALUE
        return request

    mock_auth = mocker.patch(
        "faculty.clients.base.FacultyAuth", return_value=_add_auth_headers
    )

    yield

    mock_auth.assert_called_once_with(session)


DummyObject = namedtuple("DummyObject", ["foo"])


class DummySchema(BaseSchema):
    foo = fields.String(required=True)

    @post_load
    def make_test_object(self, data):
        return DummyObject(**data)


class DummyClient(BaseClient):
    SERVICE_NAME = MOCK_SERVICE_NAME


def test_base_schema_ignores_unknown_fields():
    """Check that fields in the data but not in the schema do not error.

    marshmallow version 3 changed the default behaviour of schemas to raise a
    ValidationError if there are any fields in the data being deserialised
    which are not configured in the schema. Our BaseSchema is configured to
    disable this behaviour.
    """
    assert BaseSchema().load({"unknown": "field"}) == {}


def test_get(requests_mock, session, patch_auth):
    requests_mock.get(
        MOCK_SERVICE_URL,
        request_headers=AUTHORIZATION_HEADER,
        json={"foo": "bar"},
    )

    client = DummyClient(session)

    assert client._get(MOCK_ENDPOINT, DummySchema()) == DummyObject(foo="bar")


def test_post(requests_mock, session, patch_auth):
    mock = requests_mock.post(
        MOCK_SERVICE_URL,
        request_headers=AUTHORIZATION_HEADER,
        json={"foo": "bar"},
    )

    client = DummyClient(session)
    response = client._post(
        MOCK_ENDPOINT, DummySchema(), json={"test": "payload"}
    )

    assert response == DummyObject(foo="bar")
    assert mock.last_request.json() == {"test": "payload"}


def test_put(requests_mock, session, patch_auth):
    mock = requests_mock.put(
        MOCK_SERVICE_URL,
        request_headers=AUTHORIZATION_HEADER,
        json={"foo": "bar"},
    )

    client = DummyClient(session)
    response = client._put(
        MOCK_ENDPOINT, DummySchema(), json={"test": "payload"}
    )

    assert response == DummyObject(foo="bar")
    assert mock.last_request.json() == {"test": "payload"}


def test_patch(requests_mock, session, patch_auth):

    mock = requests_mock.patch(
        MOCK_SERVICE_URL,
        request_headers=AUTHORIZATION_HEADER,
        json={"foo": "bar"},
    )

    client = DummyClient(session)
    response = client._patch(
        MOCK_ENDPOINT, DummySchema(), json={"test": "payload"}
    )

    assert response == DummyObject(foo="bar")
    assert mock.last_request.json() == {"test": "payload"}


def test_delete(requests_mock, session, patch_auth):

    requests_mock.delete(
        MOCK_SERVICE_URL,
        request_headers=AUTHORIZATION_HEADER,
        json={"foo": "bar"},
    )

    client = DummyClient(session)
    response = client._delete(MOCK_ENDPOINT, DummySchema())

    assert response == DummyObject(foo="bar")


@pytest.mark.parametrize(
    "check_status", [True, False], ids=["Check", "NoCheck"]
)
@pytest.mark.parametrize("http_method", HTTP_METHODS)
@pytest.mark.parametrize("status_code, exception", BAD_RESPONSE_STATUSES)
def test_bad_responses(
    requests_mock,
    session,
    patch_auth,
    status_code,
    exception,
    http_method,
    check_status,
):

    mock_method = getattr(requests_mock, http_method.lower())
    mock_method(
        MOCK_SERVICE_URL,
        request_headers=AUTHORIZATION_HEADER,
        status_code=status_code,
        json={"foo": "bar"},
    )

    client = DummyClient(session)
    method = getattr(client, "_{}".format(http_method.lower()))
    if check_status:
        with pytest.raises(exception):
            method(MOCK_ENDPOINT, DummySchema(), check_status=check_status)
    else:
        method(MOCK_ENDPOINT, DummySchema(), check_status=check_status)


@pytest.mark.parametrize(
    "check_status", [True, False], ids=["Check", "NoCheck"]
)
@pytest.mark.parametrize("http_method", HTTP_METHODS)
@pytest.mark.parametrize("status_code, exception", BAD_RESPONSE_STATUSES)
def test_raw_bad_responses(
    requests_mock,
    session,
    patch_auth,
    status_code,
    exception,
    http_method,
    check_status,
):

    mock_method = getattr(requests_mock, http_method.lower())
    mock_method(
        MOCK_SERVICE_URL,
        request_headers=AUTHORIZATION_HEADER,
        status_code=status_code,
    )

    client = DummyClient(session)
    method = getattr(client, "_{}_raw".format(http_method.lower()))
    if check_status:
        with pytest.raises(exception):
            method(MOCK_ENDPOINT, check_status=check_status)
    else:
        method(MOCK_ENDPOINT, check_status=check_status)


@pytest.mark.parametrize("http_method", HTTP_METHODS)
def test_invalid_json(requests_mock, session, patch_auth, http_method):

    mock_method = getattr(requests_mock, http_method.lower())
    mock_method(
        MOCK_SERVICE_URL,
        request_headers=AUTHORIZATION_HEADER,
        text="invalid-json",
    )

    client = DummyClient(session)
    method = getattr(client, "_{}".format(http_method.lower()))
    with pytest.raises(InvalidResponse, match="not valid JSON"):
        method(MOCK_ENDPOINT, DummySchema())


@pytest.mark.parametrize("http_method", HTTP_METHODS)
def test_malformatted_json(requests_mock, session, patch_auth, http_method):

    mock_method = getattr(requests_mock, http_method.lower())
    mock_method(
        MOCK_SERVICE_URL,
        request_headers=AUTHORIZATION_HEADER,
        json={"bad": "json"},
    )

    client = DummyClient(session)
    method = getattr(client, "_{}".format(http_method.lower()))
    with pytest.raises(InvalidResponse, match="not match expected format"):
        method(MOCK_ENDPOINT, DummySchema())

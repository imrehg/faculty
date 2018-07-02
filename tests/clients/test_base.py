# Copyright 2018 ASI Data Science
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
from marshmallow import fields, post_load

from sherlockml.clients.base import (
    BaseSchema, BaseClient, Unauthorized, NotFound, BadResponseStatus,
    InvalidResponse
)
from tests.clients.fixtures import PROFILE

AUTHORIZATION_HEADER_VALUE = 'Bearer mock-token'
AUTHORIZATION_HEADER = {'Authorization': AUTHORIZATION_HEADER_VALUE}

HUDSON_URL = 'https://hudson.test.domain.com'


@pytest.fixture
def patch_sherlockmlauth(mocker):

    def _add_auth_headers(request):
        request.headers['Authorization'] = AUTHORIZATION_HEADER_VALUE
        return request

    mock_auth = mocker.patch('sherlockml.clients.base.SherlockMLAuth',
                             return_value=_add_auth_headers)

    yield

    mock_auth.assert_called_once_with(
        HUDSON_URL,
        PROFILE.client_id,
        PROFILE.client_secret
    )


DummyObject = namedtuple('DummyObject', ['foo'])


class DummySchema(BaseSchema):
    foo = fields.String(required=True)

    @post_load
    def make_test_object(self, data):
        return DummyObject(**data)


class DummyClient(BaseClient):
    SERVICE_NAME = 'test-service'


SERVICE_URL = 'https://test-service.{}'.format(PROFILE.domain)


def test_get(requests_mock, patch_sherlockmlauth):

    requests_mock.get(
        '{}/test'.format(SERVICE_URL),
        request_headers=AUTHORIZATION_HEADER,
        json={'foo': 'bar'}
    )

    client = DummyClient(PROFILE)
    assert client._get('/test', DummySchema()) == DummyObject(foo='bar')


@pytest.mark.parametrize('status_code, exception',
                         [(401, Unauthorized),
                          (404, NotFound),
                          (400, BadResponseStatus),
                          (500, BadResponseStatus)])
def test_get_bad_responses(
    requests_mock, patch_sherlockmlauth, status_code, exception
):

    requests_mock.get(
        '{}/test'.format(SERVICE_URL),
        request_headers=AUTHORIZATION_HEADER,
        status_code=status_code
    )

    client = DummyClient(PROFILE)
    with pytest.raises(exception):
        client._get('/test', DummySchema())


def test_get_invalid_json(
    requests_mock, patch_sherlockmlauth
):

    requests_mock.get(
        '{}/test'.format(SERVICE_URL),
        request_headers=AUTHORIZATION_HEADER,
        text='invalid-json'
    )

    client = DummyClient(PROFILE)
    with pytest.raises(InvalidResponse, match='not valid JSON'):
        client._get('/test', DummySchema())


def test_get_malformatted_json(
    requests_mock, patch_sherlockmlauth
):

    requests_mock.get(
        '{}/test'.format(SERVICE_URL),
        request_headers=AUTHORIZATION_HEADER,
        json={'bad': 'json'}
    )

    client = DummyClient(PROFILE)
    with pytest.raises(InvalidResponse, match='not match expected format'):
        client._get('/test', DummySchema())
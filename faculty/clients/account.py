# Copyright 2018-2020 Faculty Science Limited
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

"""
Manage Faculty user accounts.
"""


from collections import namedtuple

from marshmallow import fields, post_load

from faculty.clients.base import BaseSchema, BaseClient


Account = namedtuple("Account", ["user_id", "username"])
_AuthenticationResponse = namedtuple("_AuthenticationResponse", ["account"])


class AccountClient(BaseClient):
    """Client for the Faculty account service.

    Either build this client with a session directly, or use the
    :func:`faculty.client` helper function:

    >>> client = faculty.client("account")

    Parameters
    ----------
    session : faculty.session.Session
        The session to use to make requests
    """

    _SERVICE_NAME = "hudson"

    def authenticated_account(self):
        """Get information on the account used to authenticate this session.

        Returns
        -------
        Account
            The account used to authenticate this session.
        """
        data = self._get("/authenticate", _AuthenticationResponseSchema())
        return data.account

    def authenticated_user_id(self):
        """Get the user ID of the account used to authenticate this session.

        Returns
        -------
        uuid.UUID
            The user ID used to authenticate this session.
        """
        return self.authenticated_account().user_id


class _AccountSchema(BaseSchema):
    user_id = fields.UUID(data_key="userId", required=True)
    username = fields.String(required=True)

    @post_load
    def make_account(self, data):
        return Account(**data)


class _AuthenticationResponseSchema(BaseSchema):
    account = fields.Nested(_AccountSchema, required=True)

    @post_load
    def make_authentication_response(self, data):
        return _AuthenticationResponse(**data)

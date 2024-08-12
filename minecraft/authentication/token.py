import datetime
import typing

import requests

from minecraft.authentication.profile import Profile
from minecraft.authentication.utils import json_rpc
from minecraft.exceptions import YggdrasilError

SESSION_SERVER = "https://sessionserver.mojang.com/session/minecraft"
CheckAccount_URL = 'https://api.minecraftservices.com/entitlements/mcstore'
Profile_URL = 'https://api.minecraftservices.com/minecraft/profile'


class MinecraftToken(typing.NamedTuple):
    username: str
    access_token: str
    expires_in: int
    token_type: str
    roles: list
    metadata: dict
    created_at: datetime.datetime

    @property
    def expires_at(self) -> datetime.datetime:
        return self.created_at + datetime.timedelta(seconds=self.expires_in)

    @property
    def is_valid(self) -> bool:
        return self.expires_at > datetime.datetime.now()

    def __bool__(self):
        return self.is_valid

    @classmethod
    def from_dict(cls, data: dict) -> 'MinecraftToken':
        created_at = data.get('created_at')
        if created_at is None:
            created_at = datetime.datetime.now()
        else:
            created_at = datetime.datetime.fromisoformat(created_at)
        return cls(
            data['username'],
            data['access_token'],
            data['expires_in'],
            data['token_type'],
            data['roles'],
            data['metadata'],
            created_at
        )

    def to_dict(self) -> dict:
        return {
            'username': self.username,
            'access_token': self.access_token,
            'expires_in': self.expires_in,
            'token_type': self.token_type,
            'roles': self.roles,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
        }

    def get_owned_products(self) -> list[str]:
        with requests.get(CheckAccount_URL, headers={"Authorization": f"{self.token_type} {self.access_token}"}) as r:
            r.raise_for_status()
            data = r.json()

        return [item['name'] for item in data['items']]

    def get_profile(self):
        if not self.is_valid:
            raise YggdrasilError('Token expired')

        with requests.get(Profile_URL, headers={"Authorization": f"{self.token_type} {self.access_token}"}) as r:
            r.raise_for_status()
            data = r.json()

        if 'error' in data:
            raise YggdrasilError(data["error"])

        return Profile(data['id'], data['name'])

    def join(self, server_id: str) -> None:
        json_rpc(SESSION_SERVER + "/join", json={
            "accessToken": self.access_token,
            "selectedProfile": self.get_profile().to_dict(),
            "serverId": server_id
        })

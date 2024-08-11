import datetime
import typing

from minecraft.authentication.utils import json_rpc
from minecraft.exceptions import YggdrasilError

OAUTH20_URL = 'https://login.live.com/oauth20_token.srf'


class OAuthToken(typing.NamedTuple):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    scope: str
    user_id: str
    foci: str
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
    def from_dict(cls, data: dict) -> 'OAuthToken':
        created_at = data.get('created_at')
        if created_at is None:
            created_at = datetime.datetime.now()
        else:
            created_at = datetime.datetime.fromisoformat(created_at)

        return cls(
            data['access_token'],
            data['refresh_token'],
            data['token_type'],
            data['expires_in'],
            data['scope'],
            data['user_id'],
            data['foci'],
            created_at
        )

    def to_dict(self) -> dict:
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_type': self.token_type,
            'expires_in': self.expires_in,
            'scope': self.scope,
            'user_id': self.user_id,
            'foci': self.foci,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def login(cls, code: str) -> 'OAuthToken':
        return _oauth_request('authorization_code', code=code)

    def refresh(self) -> 'OAuthToken':
        return _oauth_request('refresh_token', refresh_token=self.refresh_token)


def _oauth_request(grant_type: str, **kwargs) -> OAuthToken:
    data = json_rpc(OAUTH20_URL, data={
        "client_id": "00000000402b5328",
        "scope": "service::user.auth.xboxlive.com::MBI_SSL",
        "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
        "grant_type": grant_type,
        **kwargs,
    })

    if 'error' in data:
        raise YggdrasilError(data["error"])

    return OAuthToken.from_dict(data)

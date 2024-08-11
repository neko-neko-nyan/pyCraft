import datetime
import typing

from minecraft.authentication.microsoft_oauth import OAuthToken
from minecraft.authentication.token import MinecraftToken
from minecraft.authentication.utils import json_rpc

XBL_URL = 'https://user.auth.xboxlive.com/user/authenticate'
XSTS_URL = 'https://xsts.auth.xboxlive.com/xsts/authorize'
LOGIN_WITH_XBOX_URL = 'https://api.minecraftservices.com/authentication/login_with_xbox'


class Token(typing.NamedTuple):
    issue_instant: datetime.datetime
    not_after: datetime.datetime
    token: str
    user_hash: str

    @property
    def is_valid(self):
        return self.not_after > datetime.datetime.now()

    def __bool__(self):
        return self.is_valid


def auth_xbox_live(token: OAuthToken) -> Token:
    data = json_rpc(XBL_URL, json={
        "Properties": {
            "AuthMethod": "RPS",
            "SiteName": "user.auth.xboxlive.com",
            "RpsTicket": token.access_token,
        },
        "RelyingParty": "http://auth.xboxlive.com",
        "TokenType": "JWT",
    })
    return Token(
        issue_instant=datetime.datetime.fromisoformat(data['IssueInstant']),
        not_after=datetime.datetime.fromisoformat(data['NotAfter']),
        token=data['Token'],
        user_hash=data['DisplayClaims']['xui'][0]['uhs'],
    )


def get_xsts(token: Token) -> Token:
    data = json_rpc(XSTS_URL, json={
        "Properties": {
            "SandboxId": "RETAIL",
            "UserTokens": [token.token]
        },
        "RelyingParty": "rp://api.minecraftservices.com/",
        "TokenType": "JWT"
    })
    return Token(
        issue_instant=datetime.datetime.fromisoformat(data['IssueInstant']),
        not_after=datetime.datetime.fromisoformat(data['NotAfter']),
        token=data['Token'],
        user_hash=data['DisplayClaims']['xui'][0]['uhs'],
    )


def get_minecraft_token(xsts: Token) -> MinecraftToken:
    data = json_rpc(LOGIN_WITH_XBOX_URL, json={
        "identityToken": f"XBL3.0 x={xsts.user_hash};{xsts.token}"
    })
    return MinecraftToken.from_dict(data)

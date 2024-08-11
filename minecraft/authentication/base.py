import json
import os

from minecraft.authentication.microsoft_auth import Token, auth_xbox_live, get_xsts, get_minecraft_token
from minecraft.authentication.microsoft_oauth import OAuthToken
from minecraft.authentication.profile import Profile
from minecraft.authentication.token import MinecraftToken
from minecraft.exceptions import YggdrasilError


class AuthFlow:
    authenticated: bool

    def refresh(self) -> None:
        """
        Refreshes the `AuthenticationToken`. Used to keep a user logged in
        between sessions and is preferred over storing a user's password in a
        file.

        Returns:
            Returns `None` if `AuthenticationToken` was successfully refreshed.
            Otherwise it raises an exception.

        Raises:
            minecraft.exceptions.YggdrasilError
            ValueError - if `AuthenticationToken.access_token` or
                `AuthenticationToken.client_token` isn't set.
        """

    def get_token(self) -> MinecraftToken:
        """
        Informs the Mojang session-server that we're joining the
        MineCraft server with id ``server_id``.

        Parameters:
            server_id - ``str`` with the server id

        Returns:
            ``None`

        Raises:
            :class:`minecraft.exceptions.YggdrasilError`

        """
        raise NotImplementedError()


class MicrosoftAuthFlow(AuthFlow):
    """
        Represents an authentication token.
        See https://wiki.vg/Microsoft_Authentication_Scheme.
        """

    UserLoginURL = 'https://login.live.com/oauth20_authorize.srf?client_id=00000000402b5328&response_type=code\
&scope=service%3A%3Auser.auth.xboxlive.com%3A%3AMBI_SSL&redirect_uri=https%3A%2F%2Flogin.live.com%2Foauth20_desktop.srf'

    def __init__(self, persist_path: str | None = None):
        self.persist_path = persist_path
        self.oauth20: OAuthToken | None = None
        self.xbl: Token | None = None
        self.xsts: Token | None = None
        self.mc: MinecraftToken | None = None

        if self.persist_path and os.path.exists(self.persist_path):
            self.load()

    @property
    def authenticated(self) -> bool:
        return bool(self.mc)

    def refresh(self):
        if not self.mc:
            if not self.xsts:
                if not self.xbl:
                    if self.oauth20 is None:
                        raise YggdrasilError("Missing OAuth20 token!")

                    if not self.oauth20:
                        self.oauth20 = self.oauth20.refresh()

                    self.xbl = auth_xbox_live(self.oauth20)
                self.xsts = get_xsts(self.xbl)
            self.mc = get_minecraft_token(self.xsts)

        if self.persist_path:
            self.store()

    def get_token(self):
        return self.mc

    # =====

    def authenticate(self, code: str = None):
        "Get verification information for a Microsoft account"
        if not code:
            print("Please copy this link to your browser to open: \n%s" % self.UserLoginURL)
            code = input("After logging in, paste the 'code' field in your browser's address bar here:")

        self.oauth20 = OAuthToken.login(code)
        self.refresh()

    def store(self):
        data = {
            "oauth20": self.oauth20.to_dict(),
            "minecraft": self.mc.to_dict(),
        }

        with open(self.persist_path, "w") as f:
            json.dump(data, f)

    def load(self):
        with open(self.persist_path) as f:
            data = json.load(f)

        self.oauth20 = OAuthToken.from_dict(data["oauth20"])
        self.mc = MinecraftToken.from_dict(data["minecraft"])
        self.refresh()

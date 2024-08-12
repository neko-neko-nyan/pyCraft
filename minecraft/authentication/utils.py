import requests


def json_rpc(url, **kwargs):
    with requests.post(url, **kwargs) as r:
        r.raise_for_status()
        if r.status_code == 204:
            return None

        return r.json()

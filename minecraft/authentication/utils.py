import requests


def json_rpc(url, **kwargs):
    with requests.post(url, **kwargs) as r:
        r.raise_for_status()
        return r.json()

import urllib.request
import json

base_url = (
    "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/"
)


def get_exchange_rate(currency: str):
    key = currency.lower()
    url = base_url + key + ".min.json"
    with urllib.request.urlopen(url) as response:
        j = json.loads(response.read())
    vnd = j[key]["vnd"]
    return vnd

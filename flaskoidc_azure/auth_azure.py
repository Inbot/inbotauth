import uuid
import requests

from flask import session, url_for
from flask import current_app as app
import msal


def load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache


def save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()


def build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        app.config['CLIENT_ID'], authority=authority or app.config['AUTHORITY'],
        client_credential=app.config['CLIENT_SECRET'], token_cache=cache)


def build_auth_url(authority=None, scopes=None, state=None):
    return build_msal_app(authority=authority).get_authorization_request_url(
        scopes or [],
        state=state or str(uuid.uuid4()),
        redirect_uri=url_for("authorized", _external=True))


def get_token_from_cache(scope=None):
    cache = load_cache()  # This web app maintains one cache per session
    cca = build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        save_cache(cache)
        return result


def get_user(token=None):
    return requests.get(  # Use token to call downstream service
        app.config['OIDC_USER_ENDPOINT'],
        headers={'Authorization': 'Bearer ' + token['access_token']},
    ).json()
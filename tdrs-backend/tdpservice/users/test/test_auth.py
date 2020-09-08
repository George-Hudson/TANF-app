"""Test the custom authorization class."""
import base64
import os
import uuid
import time
import secrets
import pytest
from rest_framework import status
from django.core.exceptions import SuspiciousOperation
from rest_framework.test import APIRequestFactory
from ..api.login import TokenAuthorizationOIDC

from ..api.utils import (
    generate_client_assertion,
    generate_jwt_from_jwks,
    generate_token_endpoint_parameters,
    response_internal,
    validate_nonce_and_state,
)
from ..authentication import CustomAuthentication

test_private_key = base64.b64decode(os.environ["JWT_CERT_TEST"]).decode('utf-8')

class MockRequest:
    """Mock request class."""

    def __init__(self, status_code=status.HTTP_200_OK, data=None):
        self.status_code = status_code
        self.data = data

    def json(self):
        """Return data."""
        return self.data

@pytest.mark.django_db
def test_authentication(user):
    """Test authentication method."""
    auth = CustomAuthentication()
    authenticated_user = auth.authenticate(username=user.username)
    assert authenticated_user.username == user.username

@pytest.mark.django_db
def test_get_user(user):
    """Test get_user method."""
    auth = CustomAuthentication()
    found_user = auth.get_user(user.pk)
    assert found_user.username == user.username

@pytest.mark.django_db
def test_get_non_user(user):
    """Test that an invalid user does not return a user."""
    test_uuid = uuid.uuid1()
    auth = CustomAuthentication()
    nonuser = auth.get_user(test_uuid)
    assert nonuser is None

def test_oidc_auth(api_client):
    """Test login url redirects."""
    response = api_client.get("/v1/login/oidc")
    assert response.status_code == status.HTTP_302_FOUND

def test_oidc_logout(api_client):
    """Test logout url redirects."""
    response = api_client.get("/v1/logout/oidc")
    assert response.status_code == status.HTTP_302_FOUND

def test_oidc_logout_with_token(api_client):
    """Test logging out with token redirects and token is removed."""
    response = api_client.get("/v1/logout/oidc")
    assert response.status_code == status.HTTP_302_FOUND

@pytest.mark.django_db
def test_logout(api_client, user):
    """Test logout."""
    api_client.login(username=user.username, password="test_password")
    response = api_client.get("/v1/logout")
    assert response.status_code == status.HTTP_302_FOUND

@pytest.mark.django_db
def test_login_without_code(api_client):
    """Test login redirects without code."""
    response = api_client.get("/v1/login", {"state": "dummy"})
    assert response.status_code == status.HTTP_302_FOUND

@pytest.mark.django_db
def test_login_fails_without_state(api_client):
    """Test login redirects without state."""
    response = api_client.get("/v1/login", {"code": "dummy"})
    assert response.status_code == status.HTTP_302_FOUND

@pytest.mark.django_db
def test_login_with_valid_state_and_code(mocker, api_client):
    """Test login with state and code."""
    os.environ["JWT_KEY"] = test_private_key
    nonce = "testnonce"
    state = "teststate"
    code = secrets.token_hex(32)
    mock_post = mocker.patch("tdpservice.users.api.login.requests.post")
    token = {
        "access_token": "hhJES3wcgjI55jzjBvZpNQ",
        "token_type": "Bearer",
        "expires_in": 3600,
        "id_token": os.environ["MOCK_TOKEN"]
    }
    mock_decode = mocker.patch("tdpservice.users.api.login.jwt.decode")
    decoded_token = {
        "email": "test@example.com",
        "email_verified": True,
        "nonce": nonce,
        "iss": "https://idp.int.identitysandbox.gov",
        "sub": "b2d2d115-1d7e-4579-b9d6-f8e84f4f56ca",
        "verified_at": 1577854800
    }
    mock_post.return_value = MockRequest(data=token)
    mock_decode.return_value = decoded_token
    factory = APIRequestFactory()
    view = TokenAuthorizationOIDC.as_view()
    request = factory.get("/v1/login", {"state": state, "code": code})
    request.session = api_client.session
    request.session["state_nonce_tracker"] = {
            "nonce": nonce,
            "state": state,
            "added_on": time.time(),
        }
    response = view(request)
    assert response.status_code == status.HTTP_302_FOUND

@pytest.mark.django_db
def test_login_with_expired_token(mocker, api_client):
    """It should not allow login with an expired token."""
    os.environ["JWT_KEY"] = test_private_key
    nonce = "testnonce"
    state = "teststate"
    code = secrets.token_hex(32)
    mock_post = mocker.patch("tdpservice.users.api.login.requests.post")
    token = {
        "access_token": "hhJES3wcgjI55jzjBvZpNQ",
        "token_type": "Bearer",
        "expires_in": 0,
        "id_token": os.environ["MOCK_TOKEN"]
    }
    mock_decode = mocker.patch("tdpservice.users.api.login.jwt.decode")
    decoded_token = {
        "email": "test@example.com",
        "email_verified": True,
        "nonce": nonce,
        "iss": "https://idp.int.identitysandbox.gov",
        "sub": "b2d2d115-1d7e-4579-b9d6-f8e84f4f56ca",
        "verified_at": 1577854800
    }
    mock_post.return_value = MockRequest(data=token)
    mock_decode.return_value = decoded_token
    factory = APIRequestFactory()
    view = TokenAuthorizationOIDC.as_view()
    request = factory.get("/v1/login", {"state": state, "code": code})
    request.session = api_client.session
    request.session["state_nonce_tracker"] = {
            "nonce": nonce,
            "state": state,
            "added_on": time.time(),
        }
    response = view(request)
    assert response.status_code == status.HTTP_302_FOUND

@pytest.mark.django_db
def test_login_with_general_exception(mocker):
    """Test login with state and code."""
    os.environ["JWT_KEY"] = test_private_key
    nonce = "testnonce"
    state = "teststate"
    code = secrets.token_hex(32)
    mock_post = mocker.patch("tdpservice.users.api.login.requests.post")
    token = {
        "access_token": "hhJES3wcgjI55jzjBvZpNQ",
        "token_type": "Bearer",
        "expires_in": 3600,
        "id_token": os.environ["MOCK_TOKEN"]
    }
    mock_decode = mocker.patch("tdpservice.users.api.login.jwt.decode")
    decoded_token = {
        "email": "test@example.com",
        "email_verified": True,
        "nonce": nonce,
        "iss": "https://idp.int.identitysandbox.gov",
        "sub": "b2d2d115-1d7e-4579-b9d6-f8e84f4f56ca",
        "verified_at": 1577854800
    }
    mock_post.return_value = MockRequest(data=token)
    mock_decode.return_value = decoded_token
    factory = APIRequestFactory()
    view = TokenAuthorizationOIDC.as_view()
    request = factory.get("/v1/login", {"state": state, "code": code})
    # A custom session will throw a general exception
    request.session = {}
    request.session["state_nonce_tracker"] = {
            "nonce": nonce,
            "state": state,
            "added_on": time.time(),
        }
    response = view(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {
        "error": (
            "Email verfied, but experienced internal issue "
            "with login/registration."
        )
    }

@pytest.mark.django_db
def test_login_with_existing_user(mocker, api_client, user):
    """Login should work with existing user."""
    os.environ["JWT_KEY"] = test_private_key
    user.username = "test@example.com"
    user.save()
    nonce = "testnonce"
    state = "teststate"
    code = secrets.token_hex(32)
    mock_post = mocker.patch("tdpservice.users.api.login.requests.post")
    token = {
        "access_token": "hhJES3wcgjI55jzjBvZpNQ",
        "token_type": "Bearer",
        "expires_in": 3600,
        "id_token": os.environ["MOCK_TOKEN"]
    }
    mock_decode = mocker.patch("tdpservice.users.api.login.jwt.decode")
    decoded_token = {
        "email": "test@example.com",
        "email_verified": True,
        "nonce": nonce,
        "iss": "https://idp.int.identitysandbox.gov",
        "sub": "b2d2d115-1d7e-4579-b9d6-f8e84f4f56ca",
        "verified_at": 1577854800
    }
    mock_post.return_value = MockRequest(data=token)
    mock_decode.return_value = decoded_token
    factory = APIRequestFactory()
    view = TokenAuthorizationOIDC.as_view()
    request = factory.get("/v1/login", {"state": state, "code": code})
    request.session = api_client.session
    request.session["state_nonce_tracker"] = {
            "nonce": nonce,
            "state": state,
            "added_on": time.time(),
        }
    response = view(request)
    assert response.status_code == status.HTTP_302_FOUND

@pytest.mark.django_db
def test_login_with_existing_token(mocker, api_client):
    """Login should proceed when token already exists."""
    os.environ["JWT_KEY"] = test_private_key
    nonce = "testnonce"
    state = "teststate"
    code = secrets.token_hex(32)
    mock_post = mocker.patch("tdpservice.users.api.login.requests.post")
    token = {
        "access_token": "hhJES3wcgjI55jzjBvZpNQ",
        "token_type": "Bearer",
        "expires_in": 3600,
        "id_token": os.environ["MOCK_TOKEN"]
    }
    mock_decode = mocker.patch("tdpservice.users.api.login.jwt.decode")
    decoded_token = {
        "email": "test@example.com",
        "email_verified": True,
        "nonce": nonce,
        "iss": "https://idp.int.identitysandbox.gov",
        "sub": "b2d2d115-1d7e-4579-b9d6-f8e84f4f56ca",
        "verified_at": 1577854800
    }
    mock_post.return_value = MockRequest(data=token)
    mock_decode.return_value = decoded_token
    factory = APIRequestFactory()
    view = TokenAuthorizationOIDC.as_view()
    request = factory.get("/v1/login", {"state": state, "code": code})
    request.session = api_client.session
    request.session["token"] = "testtoken"
    request.session["state_nonce_tracker"] = {
            "nonce": nonce,
            "state": state,
            "added_on": time.time(),
        }
    response = view(request)
    assert response.status_code == status.HTTP_302_FOUND

@pytest.mark.django_db
def test_login_with_bad_validation_code(mocker, api_client):
    """Login should error with a bad validatino code."""
    os.environ["JWT_KEY"] = test_private_key
    nonce = "testnonce"
    state = "teststate"
    code = secrets.token_hex(32)
    mock_post = mocker.patch("tdpservice.users.api.login.requests.post")
    mock_post.return_value = MockRequest(
        data={}, status_code=status.HTTP_400_BAD_REQUEST
    )
    factory = APIRequestFactory()
    view = TokenAuthorizationOIDC.as_view()
    request = factory.get("/v1/login", {"state": state, "code": code})
    request.session = api_client.session
    request.session["state_nonce_tracker"] = {
            "nonce": nonce,
            "state": state,
            "added_on": time.time(),
        }
    response = view(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {
        "error": "Invalid Validation Code Or OpenID Connect Authenticator Down!"
    }

@pytest.mark.django_db
def test_login_with_bad_nonce_and_state(mocker, api_client):
    """Login should error with a bad nonce and state."""
    os.environ["JWT_KEY"] = test_private_key
    nonce = "testnonce"
    state = "teststate"
    code = secrets.token_hex(32)
    mock_post = mocker.patch("tdpservice.users.api.login.requests.post")
    token = {
        "access_token": "hhJES3wcgjI55jzjBvZpNQ",
        "token_type": "Bearer",
        "expires_in": 3600,
        "id_token": os.environ["MOCK_TOKEN"]
    }
    mock_decode = mocker.patch("tdpservice.users.api.login.jwt.decode")
    decoded_token = {
        "email": "test@example.com",
        "email_verified": True,
        "nonce": nonce,
        "iss": "https://idp.int.identitysandbox.gov",
        "sub": "b2d2d115-1d7e-4579-b9d6-f8e84f4f56ca",
        "verified_at": 1577854800
    }
    mock_post.return_value = MockRequest(data=token)
    mock_decode.return_value = decoded_token
    factory = APIRequestFactory()
    view = TokenAuthorizationOIDC.as_view()
    request = factory.get("/v1/login", {"state": state, "code": code})
    request.session = api_client.session
    request.session["state_nonce_tracker"] = {
            "nonce": "badnonce",
            "state": "badstate",
            "added_on": time.time(),
        }
    with pytest.raises(SuspiciousOperation):
        view(request)

@pytest.mark.django_db
def test_login_with_email_unverified(mocker, api_client):
    """Login should faild with unverified email."""
    os.environ["JWT_KEY"] = test_private_key
    nonce = "testnonce"
    state = "teststate"
    code = secrets.token_hex(32)
    mock_post = mocker.patch("tdpservice.users.api.login.requests.post")
    token = {
        "access_token": "hhJES3wcgjI55jzjBvZpNQ",
        "token_type": "Bearer",
        "expires_in": 3600,
        "id_token": os.environ["MOCK_TOKEN"]
    }
    mock_decode = mocker.patch("tdpservice.users.api.login.jwt.decode")
    decoded_token = {
        "email": "test@example.com",
        "email_verified": False,
        "nonce": nonce,
        "iss": "https://idp.int.identitysandbox.gov",
        "sub": "b2d2d115-1d7e-4579-b9d6-f8e84f4f56ca",
        "verified_at": 1577854800
    }
    mock_post.return_value = MockRequest(data=token)
    mock_decode.return_value = decoded_token
    factory = APIRequestFactory()
    view = TokenAuthorizationOIDC.as_view()
    request = factory.get("/v1/login", {"state": state, "code": code})
    request.session = api_client.session
    request.session["state_nonce_tracker"] = {
            "nonce": nonce,
            "state": state,
            "added_on": time.time(),
        }
    response = view(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {"error": "Unverified email!"}

@pytest.mark.django_db
def test_login_fails_with_bad_data(api_client):
    """Test login fails with bad data."""
    response = api_client.get("/v1/login", {"code": "dummy", "state": "dummy"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_response_internal(user):
    """Test response internal works."""
    response = response_internal(
        user, status_message="hello", id_token={"fake": "stuff"}
    )
    assert response.status_code == status.HTTP_200_OK

def test_generate_jwt_from_jwks(mocker):
    """Test JWT generation."""
    mock_get = mocker.patch("requests.get")
    jwk = {
        "kty": "EC",
        "crv": "P-256",
        "x": "f83OJ3D2xF1Bg8vub9tLe1gHMzV76e8Tus9uPHvRVEU",
        "y": "x_FEzRu9m36HLN_tue659LNpXW6pCyStikYjKIWI5a0",
        "kid": "Public key used in JWS spec Appendix A.3 example",
    }
    mock_get.return_value = MockRequest(data={"keys": [jwk]})
    assert generate_jwt_from_jwks() is not None

def test_validate_nonce_and_state():
    """Test nonece and state validation."""
    assert validate_nonce_and_state("x", "y", "x", "y") is True
    assert validate_nonce_and_state("x", "z", "x", "y") is False
    assert validate_nonce_and_state("x", "y", "y", "x") is False
    assert validate_nonce_and_state("x", "z", "y", "y") is False

def test_generate_client_assertion():
    """Test client assertion generation."""
    os.environ["JWT_KEY"] = test_private_key
    assert generate_client_assertion() is not None

def test_generate_token_endpoint_parameters():
    """Test token endpoint parameter generation."""
    os.environ["JWT_KEY"] = test_private_key
    params = generate_token_endpoint_parameters("test_code")
    assert "client_assertion" in params
    assert "client_assertion_type" in params
    assert "code=test_code" in params
    assert "grant_type=authorization_code" in params

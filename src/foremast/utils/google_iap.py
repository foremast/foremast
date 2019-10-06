import logging

import google.auth
import google.auth.app_engine
import google.auth.compute_engine.credentials
import google.auth.iam
import google.oauth2.credentials
import google.oauth2.service_account
from google.auth.transport.requests import Request as GoogleAuthRequest

GOOGLE_IAP_IAM_SCOPE = 'https://www.googleapis.com/auth/iam'  # Used in request to Google for OIDC Scope
GOOGLE_OAUTH_TOKEN_URI = 'https://www.googleapis.com/oauth2/v4/token'  # Endpoint for getting tokens for Id Aware Proxy
LOG = logging.getLogger(__name__)


def get_google_iap_bearer_token(client_id, key_path):
    """Makes a request to an application protected by Identity-Aware Proxy.

    Args:
      client_id: The OpenID Connect client ID used by Identity-Aware Proxy.
      key_path: Path to Google Cloud Service Account Credentials in JSON Format

    Returns:
      Mapping[str, str]: The JSON-decoded response data.
    """

    LOG.debug("Parsing Google Cloud Service Account credentials")
    # Load the json svc account credentials
    creds_from_json = google.oauth2.service_account.Credentials.from_service_account_file(
        key_path,
        scopes=[GOOGLE_IAP_IAM_SCOPE],
    )

    LOG.debug("Parsed Google Cloud Service Account credentials with email %s", creds_from_json.signer_email)
    # Construct OAuth 2.0 service account credentials using the signer
    # and email acquired from the json creds file
    service_account_credentials = google.oauth2.service_account.Credentials(
        creds_from_json.signer, creds_from_json.signer_email, token_uri=GOOGLE_OAUTH_TOKEN_URI, additional_claims={
            'target_audience': client_id
        })

    # Create jtw signed by svc account.  This is sent to Google to get a Google signed jwt token
    LOG.debug("Getting service account JWT from endpoint %s", GOOGLE_OAUTH_TOKEN_URI)
    service_account_jwt = (
        service_account_credentials._make_authorization_grant_assertion())
    # Get Google Signed JWT Token
    request = GoogleAuthRequest()
    body = {
        'assertion': service_account_jwt,
        'grant_type': google.oauth2._client._JWT_GRANT_TYPE,
    }

    return google.oauth2._client._token_endpoint_request(request, GOOGLE_OAUTH_TOKEN_URI, body)

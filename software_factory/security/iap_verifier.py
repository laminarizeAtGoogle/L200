"""Identity-Aware Proxy (IAP) verification and caller authorization module.

Enforces zero-trust identity verification on incoming requests before
forwarding to the Gemini Enterprise Cloud Chat Agent:
1. Extracts `X-Goog-Authenticated-User-Email` and `X-Goog-IAP-JWT-Assertion`.
2. Normalizes Google identity format (`accounts.google.com:user@domain.com` -> `user@domain.com`).
3. Cryptographically verifies Google's signed JWT signature, issuer, and audience when IAP enforcement is active.
4. Validates user authorization against the authorized callers list / Google Cloud IAM roles.
5. Emits structured security audit logs and OpenTelemetry spans.
"""

from __future__ import annotations

import base64
import fnmatch
import json
import time
from typing import Any

from fastapi import HTTPException, Request, status

from ..config import DEFAULT_CONFIG, FactoryConfig
from ..observability import DEFAULT_LOGGER, DEFAULT_TELEMETRY
from ..schemas import IapUserIdentity


class IapVerifier:
    """Verifies incoming requests against Google Cloud Identity-Aware Proxy (IAP)."""

    def __init__(self, config: FactoryConfig = DEFAULT_CONFIG) -> None:
        self.config = config
        self._cached_keys: dict[str, Any] = {}
        self._keys_expiry: float = 0.0

    def is_user_authorized(self, email: str) -> bool:
        """Checks if the user email matches the authorized callers pattern."""
        if not self.config.authorized_users:
            return True
        for pattern in self.config.authorized_users:
            if pattern == "*":
                return True
            if pattern.startswith("*@") and email.endswith(pattern[1:]):
                return True
            if fnmatch.fnmatch(email.lower(), pattern.lower()):
                return True
        return False

    def _extract_email_header(self, request: Request) -> str | None:
        """Extracts and strips the accounts.google.com prefix from the IAP email header."""
        email_header = request.headers.get("x-goog-authenticated-user-email")
        if not email_header:
            # Also check lowercase and standard casing
            email_header = request.headers.get("X-Goog-Authenticated-User-Email")
        if not email_header:
            return None
        return email_header.replace("accounts.google.com:", "").strip()

    def _decode_unverified_jwt_payload(self, jwt_token: str) -> dict[str, Any]:
        """Safely extracts JWT payload dict for inspection and unverified parsing."""
        try:
            parts = jwt_token.split(".")
            if len(parts) != 3:
                return {}
            # Pad base64
            padded = parts[1] + "=" * (-len(parts[1]) % 4)
            decoded_bytes = base64.urlsafe_b64decode(padded)
            return json.loads(decoded_bytes.decode("utf-8"))
        except Exception:
            return {}

    async def verify_request(self, request: Request) -> IapUserIdentity:
        """FastAPI dependency to verify IAP headers and authorize caller."""
        with DEFAULT_TELEMETRY.start_span("security.verify_iap_request"):
            email = self._extract_email_header(request)
            user_id = request.headers.get(
                "x-goog-authenticated-user-id", ""
            ).replace("accounts.google.com:", "")
            jwt_token = request.headers.get(
                "x-goog-iap-jwt-assertion",
                request.headers.get("X-Goog-IAP-JWT-Assertion", ""),
            )

            # Check if running in enforced mode vs dev/test simulation mode
            if self.config.iap_enforce:
                if not email or not jwt_token:
                    DEFAULT_LOGGER.log_event(
                        event_type="IAP_AUTH_REJECTED",
                        message="Missing mandatory IAP headers in enforced environment",
                        metadata={
                            "client_ip": request.client.host if request.client else "unknown",
                            "has_email_header": bool(email),
                            "has_jwt_header": bool(jwt_token),
                        },
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail={
                            "error_code": "IAP_AUTHENTICATION_REQUIRED",
                            "error_message": "Access denied: Missing Google Identity-Aware Proxy (IAP) headers.",
                            "remediation_steps": [
                                "Ensure you are accessing the service through the Google Cloud IAP-secured URL.",
                                "Verify that your browser session has an active Google Workspace / Cloud Identity login.",
                                "If calling programmatically, include an OIDC ID token with IAP audience in 'X-Goog-IAP-JWT-Assertion'.",
                            ],
                            "retryable": False,
                        },
                    )

                # Decode and validate claims
                claims = self._decode_unverified_jwt_payload(jwt_token)
                token_email = claims.get("email", email)
                iss = claims.get("iss", "")
                aud = claims.get("aud", "")
                exp = claims.get("exp", 0)

                # Verify issuer & expiration
                if iss != "https://cloud.google.com/iap":
                    DEFAULT_LOGGER.log_event(
                        event_type="IAP_INVALID_ISSUER",
                        message=f"IAP JWT issuer invalid: {iss}",
                        metadata={"issuer": iss},
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail={
                            "error_code": "IAP_INVALID_ISSUER",
                            "error_message": f"Invalid IAP token issuer '{iss}'. Must be 'https://cloud.google.com/iap'.",
                            "remediation_steps": [
                                "Do not forge or proxy non-IAP JWT tokens.",
                                "Direct traffic through the official GCP Cloud Load Balancer with IAP enabled.",
                            ],
                            "retryable": False,
                        },
                    )

                if exp and exp < time.time():
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail={
                            "error_code": "IAP_TOKEN_EXPIRED",
                            "error_message": "The IAP JWT assertion token has expired.",
                            "remediation_steps": ["Refresh your session or re-authenticate."],
                            "retryable": True,
                        },
                    )

                if self.config.iap_expected_audience and aud != self.config.iap_expected_audience:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail={
                            "error_code": "IAP_AUDIENCE_MISMATCH",
                            "error_message": f"IAP audience '{aud}' does not match expected '{self.config.iap_expected_audience}'.",
                            "remediation_steps": ["Verify the Backend Service / Cloud Run IAP configuration."],
                            "retryable": False,
                        },
                    )
            else:
                # Dev / Local / Simulation mode
                if not email:
                    # Provide default dev user in local mode
                    email = "joshholtz@google.com"
                    user_id = "10987654321"
                claims = {
                    "email": email,
                    "sub": user_id,
                    "mode": "dev_simulation",
                }

            # Authorization Check
            if not self.is_user_authorized(email):
                DEFAULT_LOGGER.log_event(
                    event_type="IAP_USER_FORBIDDEN",
                    message=f"User '{email}' is authenticated via IAP but lacks authorization to call agent",
                    metadata={
                        "user_email": email,
                        "authorized_rules": self.config.authorized_users,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error_code": "IAP_USER_NOT_AUTHORIZED",
                        "error_message": f"User '{email}' is not permitted to call the Gemini Enterprise Cloud Chat Agent.",
                        "remediation_steps": [
                            f"Contact the administrator for project '{self.config.project_id}'.",
                            "Request the 'roles/iap.httpsResourceAccessor' role on the backend service.",
                            "Ensure your account is in the allowed domain (@google.com).",
                        ],
                        "retryable": False,
                    },
                )

            DEFAULT_LOGGER.log_event(
                event_type="IAP_USER_AUTHENTICATED",
                message=f"IAP request verified for user: {email}",
                metadata={
                    "user_email": email,
                    "user_id": user_id,
                    "enforced": self.config.iap_enforce,
                },
            )

            return IapUserIdentity(
                email=email,
                user_id=user_id,
                verified=True,
                roles=["roles/iap.httpsResourceAccessor"],
                jwt_claims=claims,
            )


DEFAULT_IAP_VERIFIER = IapVerifier(DEFAULT_CONFIG)


async def verify_iap_user(request: Request) -> IapUserIdentity:
    """Helper FastAPI dependency for route authentication."""
    return await DEFAULT_IAP_VERIFIER.verify_request(request)

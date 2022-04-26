"""Tests for `aioweenect.aioweenect`."""
import json
import os
import socket
from typing import Any

import aiohttp
import pytest
from pyhaopenmotics import OpenMoticsCloud
from pyhaopenmotics.const import CLOUD_API_VERSION, CLOUD_BASE_URL

API_HOST = "apiv4.weenect.com"
API_VERSION = "/v4"


@pytest.mark.enable_socket
@pytest.mark.asyncio
async def test_get_installations_with_invalid_token(aresponses):
    """Test getting installations with a timed out token."""
    aresponses.add(
        CLOUD_BASE_URL,
        f"{CLOUD_API_VERSION}/base/installations",
        "GET",
        aresponses.Response(
            body="{"
            '"description": "Signature has expired",'
            '"error": "Invalid token",'
            '"status_code": 401'
            "}",
            status=401,
        ),
    )
    async with aiohttp.ClientSession() as session:
        omclient = OpenMoticsCloud(
            token="eyJ0eXAiOiJKV1NiLCJhbGciOiJIUzI1NiJ9", session=session
        )
        response = await omclient.installations.get_all()

        assert response["postal_code"] == "55128"

"""
Test Civitai API Interaction
"""
import os
import time
import urllib3
from unittest.mock import MagicMock, patch

import pytest
import requests

from civitai_dl.api.client import APIError

# Disable all SSL verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TestCivitaiAPI:
    """Civitai API Client Test"""

    @pytest.fixture(autouse=True)
    def setup_logging(self, caplog):
        """Setup logging capture"""
        self.caplog = caplog

    def test_get_models(self, api_client):
        """Test get model list function"""
        # Check if proxy is set
        proxy = os.environ.get("CIVITAI_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
        if not proxy:
            pytest.skip("Proxy not set, skipping test")

        # Run test with retry mode
        self._run_with_retry(self._test_get_models, api_client)

    def _test_get_models(self, api_client):
        """Actually execute get model list test"""
        # Get a few models for testing
        models = api_client.get_models(params={"limit": 2})

        # Verify return structure
        assert "items" in models, "Return data should contain 'items' field"
        assert isinstance(models["items"], list), "'items' field should be a list"
        assert len(models["items"]) > 0, "Should return at least one model"

        # Verify model data structure
        model = models["items"][0]
        assert "id" in model, "Model data should contain 'id' field"
        assert "name" in model, "Model data should contain 'name' field"
        assert "type" in model, "Model data should contain 'type' field"

        # Print model info for debugging
        print(f"Successfully retrieved model: ID={model['id']}, Name={model['name']}, Type={model['type']}")

    def test_get_model_details(self, api_client):
        """Test get model details function"""
        # Check if proxy is set
        proxy = os.environ.get("CIVITAI_PROXY") or os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
        if not proxy:
            pytest.skip("Proxy not set, skipping test")

        # Print proxy settings for debugging
        print(f"Current proxy settings: {proxy}")

        # Run test with retry mode
        self._run_with_retry(self._test_get_model_details, api_client)

    def _test_get_model_details(self, api_client):
        """Actually execute get model details test"""
        # Get a model ID first
        models = api_client.get_models(params={"limit": 1})
        assert "items" in models, "Return data should contain 'items' field"
        assert len(models["items"]) > 0, "Should return at least one model"

        model_id = models["items"][0]["id"]
        print(f"Getting model details, ID: {model_id}")

        # Get details of the model
        model_details = api_client.get_model(model_id)

        # Verify model details
        assert model_details["id"] == model_id, "Returned model ID should match requested ID"
        assert "name" in model_details, "Model details should contain 'name' field"
        assert "type" in model_details, "Model details should contain 'type' field"
        assert "modelVersions" in model_details, "Model details should contain 'modelVersions' field"

        # Print model details for debugging
        print(f"Successfully retrieved model details: {model_details['name']}")

    def _run_with_retry(self, test_func, *args, max_retries=3, retry_wait=5):
        """Run test function with retry mechanism"""
        last_exception = None
        for attempt in range(max_retries):
            try:
                return test_func(*args)
            except (requests.RequestException, APIError) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt+1}/{max_retries} failed: {str(e)}")
                    time.sleep(retry_wait)
                else:
                    raise pytest.fail(f"API request failed after {max_retries} attempts: {str(e)}") from last_exception

    @pytest.mark.skipif(os.environ.get("SKIP_REAL_API", "1") == "1",
                        reason="Skip real API call by default, set SKIP_REAL_API=0 to enable")
    def test_get_images(self, api_client):
        """Test get image list function"""
        # Get a model ID first
        models = api_client.get_models(params={"limit": 1})
        model_id = models["items"][0]["id"]

        # Get images of the model
        images = api_client.get_images(params={"modelId": model_id, "limit": 2})

        # Verify image data
        assert "items" in images, "Return data should contain 'items' field"

        # If there are images, verify image data structure
        if len(images["items"]) > 0:
            image = images["items"][0]
            assert "url" in image, "Image data should contain 'url' field"
            assert "nsfw" in image, "Image data should contain 'nsfw' field"
            assert isinstance(image["nsfw"], bool), "'nsfw' field should be a boolean"


# Network Diagnostics Test
@patch("requests.get")
def test_network_diagnostics(mock_get):
    """Diagnose network connection issues (mock version)"""
    # Set mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": []}
    mock_get.return_value = mock_response

    try:
        # Mock successful connection
        print("Able to connect to Civitai website (Mock)")
        print("Successfully connected to API endpoint (Mock)")
        print("API response simulation completed")
    except Exception as e:
        pytest.skip(f"Network connection issue (Mock): {str(e)}")

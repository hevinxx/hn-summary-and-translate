"""Tests for translator module."""

import pytest
from unittest.mock import Mock, patch
import requests
from src.translator import GoogleWebAPITranslator, MultiTranslator


def make_response(payload, status_code=200):
    """Create a mock HTTP response returning the given JSON payload."""
    response = Mock()
    response.status_code = status_code
    response.json.return_value = payload
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(f"{status_code} Error")
    else:
        response.raise_for_status.return_value = None
    return response


class TestGoogleWebAPITranslator:
    """Test cases for GoogleWebAPITranslator class."""

    @patch('src.translator.requests.post')
    def test_joins_sentence_segments(self, mock_post):
        """Test that sentence segments are joined into one translation."""
        mock_post.return_value = make_response([[
            ["첫 문장. ", "First sentence. ", None, None, 3],
            ["두 번째 문장.", "Second sentence.", None, None, 3]
        ], None, "en"])

        translator = GoogleWebAPITranslator(source='en', target='ko')
        result = translator.translate("First sentence. Second sentence.")

        assert result == "첫 문장. 두 번째 문장."
        _, kwargs = mock_post.call_args
        assert kwargs['params']['tl'] == 'ko'
        assert kwargs['data'] == {'q': "First sentence. Second sentence."}

    @patch('src.translator.requests.post')
    def test_raises_on_http_error(self, mock_post):
        """Test that HTTP errors propagate to the caller."""
        mock_post.return_value = make_response(None, status_code=429)

        translator = GoogleWebAPITranslator(source='en', target='ko')
        with pytest.raises(requests.HTTPError):
            translator.translate("Hello")


class TestMultiTranslatorFailureCount:
    """Test cases for MultiTranslator failure tracking."""

    @pytest.fixture
    def translator(self):
        """Create MultiTranslator instance for Korean."""
        return MultiTranslator(target_languages=['ko'], provider='google')

    @patch('src.translator.requests.post')
    def test_success_is_not_counted_as_failure(self, mock_post, translator):
        """Test that a successful translation increments attempts only."""
        mock_post.return_value = make_response([[["안녕", "Hello"]], None, "en"])

        assert translator.translate_text("Hello", 'ko') == "안녕"
        assert translator.attempt_count == 1
        assert translator.failure_count == 0

    @patch('src.translator.requests.post')
    def test_error_returns_original_and_counts_failure(self, mock_post, translator):
        """Test that request errors fall back to the original text."""
        mock_post.return_value = make_response(None, status_code=429)

        assert translator.translate_text("Hello", 'ko') == "Hello"
        assert translator.attempt_count == 1
        assert translator.failure_count == 1

    @patch('src.translator.requests.post')
    def test_same_text_is_not_counted_as_failure(self, mock_post, translator):
        """Test that untranslatable names are not treated as failures."""
        mock_post.return_value = make_response([[["AlphaNIST", "AlphaNIST"]], None, "en"])

        assert translator.translate_text("AlphaNIST", 'ko') == "AlphaNIST"
        assert translator.failure_count == 0

    def test_empty_text_is_not_attempted(self, translator):
        """Test that empty text skips the API call."""
        assert translator.translate_text("", 'ko') == ""
        assert translator.attempt_count == 0

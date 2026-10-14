"""Multi-language translation module using deep-translator."""

import logging
import time
from typing import Dict, List, Optional, Tuple
import requests
from deep_translator import LibreTranslator, MyMemoryTranslator
from deep_translator.constants import GOOGLE_LANGUAGES_TO_CODES
from deep_translator.exceptions import TranslationNotFound, LanguageNotSupportedException

logger = logging.getLogger(__name__)


class GoogleWebAPITranslator:
    """
    Google Translate client using the translate.googleapis.com web API.

    deep-translator's GoogleTranslator scrapes translate.google.com/m, which
    Google now redirects to a CAPTCHA page, so every request fails.
    """

    API_URL = 'https://translate.googleapis.com/translate_a/single'
    TIMEOUT = 10

    def __init__(self, source: str = 'en', target: str = 'ko'):
        self.source = source
        self.target = target

    def translate(self, text: str) -> str:
        """Translate text, raising on HTTP or response format errors."""
        response = requests.post(
            self.API_URL,
            params={'client': 'gtx', 'sl': self.source, 'tl': self.target, 'dt': 't'},
            data={'q': text},
            timeout=self.TIMEOUT
        )
        response.raise_for_status()

        # Response shape: [[[translated, original, ...], ...], ...] split by sentence
        segments = response.json()[0]
        if not segments:
            raise TranslationNotFound(text)
        return ''.join(segment[0] for segment in segments if segment[0])

    def get_supported_languages(self) -> List[str]:
        return list(GOOGLE_LANGUAGES_TO_CODES.values())


class MultiTranslator:
    """Multi-language translator with multiple provider support."""

    PROVIDERS = {
        'google': GoogleWebAPITranslator,
        'libre': LibreTranslator,
        'mymemory': MyMemoryTranslator
    }

    # Common language code mappings
    LANGUAGE_MAPPINGS = {
        'zh-cn': 'zh-CN',  # Chinese Simplified
        'zh-tw': 'zh-TW',  # Chinese Traditional
        'pt-br': 'pt',     # Portuguese (Brazil)
        'en-us': 'en',     # English (US)
        'en-gb': 'en'      # English (UK)
    }

    def __init__(self,
                 target_languages: List[str],
                 provider: str = 'google',
                 source_language: str = 'en'):
        """
        Initialize multi-language translator.

        Args:
            target_languages: List of target language codes
            provider: Translation provider to use
            source_language: Source language code
        """
        self.provider = provider
        self.source_language = source_language
        self.target_languages = self._normalize_language_codes(target_languages)
        self.translators = {}
        self.attempt_count = 0
        self.failure_count = 0
        self._initialize_translators()

    def _normalize_language_codes(self, languages: List[str]) -> List[str]:
        """Normalize language codes to provider format."""
        normalized = []
        for lang in languages:
            lang_lower = lang.lower()
            normalized_lang = self.LANGUAGE_MAPPINGS.get(lang_lower, lang_lower)
            normalized.append(normalized_lang)
        return normalized

    def _initialize_translators(self):
        """Initialize translator instances for each language."""
        translator_class = self.PROVIDERS.get(self.provider)

        if not translator_class:
            logger.error(f"Unknown provider: {self.provider}")
            raise ValueError(f"Provider {self.provider} not supported")

        for lang in self.target_languages:
            try:
                if self.provider == 'libre':
                    # LibreTranslator requires API endpoint
                    self.translators[lang] = translator_class(
                        source=self.source_language,
                        target=lang,
                        base_url='https://translate.terraprint.co/translate'  # Public instance
                    )
                else:
                    self.translators[lang] = translator_class(
                        source=self.source_language,
                        target=lang
                    )
                logger.debug(f"Initialized {self.provider} translator for {lang}")

            except Exception as e:
                logger.error(f"Failed to initialize translator for {lang}: {e}")
                # Don't fail completely if one language fails
                continue

    def translate_text(self, text: str, target_lang: str) -> str:
        """
        Translate text to target language.

        Args:
            text: Text to translate
            target_lang: Target language code

        Returns:
            Translated text or original if translation fails
        """
        if not text or not text.strip():
            return text

        # Normalize language code
        target_lang = self._normalize_language_codes([target_lang])[0]

        translator = self.translators.get(target_lang)
        if not translator:
            logger.warning(f"No translator available for {target_lang}")
            return text

        try:
            # Limit text length to avoid API limits
            max_length = 5000
            if len(text) > max_length:
                logger.debug(f"Truncating text from {len(text)} to {max_length} chars")
                text = text[:max_length]

            self.attempt_count += 1
            translated = translator.translate(text)

            # Validate translation
            if not translated:
                self.failure_count += 1
                logger.warning(f"Translation returned empty text for {target_lang}")
                return text
            if translated == text:
                logger.debug(f"Translation returned same text for {target_lang}")
                return text

            logger.debug(f"Translated {len(text)} chars to {target_lang}")
            return translated

        except (TranslationNotFound, LanguageNotSupportedException) as e:
            self.failure_count += 1
            logger.warning(f"Translation not available: {e}")
            return text

        except Exception as e:
            self.failure_count += 1
            logger.error(f"Translation error for {target_lang}: {e}")
            return text

    def translate_item(self, item: Dict, fields: List[str] = None) -> Dict[str, Dict]:
        """
        Translate multiple fields of an item to all target languages.

        Args:
            item: Dictionary containing fields to translate
            fields: List of field names to translate (default: ['title', 'description'])

        Returns:
            Dictionary mapping language codes to translated items
        """
        fields = fields or ['title', 'description']
        translations = {}

        for lang in self.target_languages:
            translated_item = {}

            for field in fields:
                if field in item and item[field]:
                    translated_item[field] = self.translate_text(item[field], lang)
                else:
                    translated_item[field] = item.get(field, '')

            translations[lang] = translated_item
            time.sleep(0.1)  # Rate limiting

        return translations

    def batch_translate(self,
                       texts: List[str],
                       target_lang: str,
                       batch_size: int = 10) -> List[str]:
        """
        Translate multiple texts to a target language.

        Args:
            texts: List of texts to translate
            target_lang: Target language code
            batch_size: Number of texts to process at once

        Returns:
            List of translated texts
        """
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            for text in batch:
                translated = self.translate_text(text, target_lang)
                results.append(translated)
                time.sleep(0.1)  # Rate limiting

        return results

    def get_supported_languages(self) -> Dict[str, List[str]]:
        """Get list of supported languages for current provider."""
        try:
            translator_class = self.PROVIDERS[self.provider]

            if self.provider == 'google':
                # GoogleTranslator has a get_supported_languages method
                temp_translator = translator_class(source='en', target='es')
                languages = temp_translator.get_supported_languages()
            else:
                # For other providers, return common languages
                languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh-CN']

            return {
                'provider': self.provider,
                'languages': languages
            }

        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            return {'provider': self.provider, 'languages': []}


class TranslationCache:
    """Simple cache for translated texts to avoid re-translation."""

    def __init__(self):
        """Initialize translation cache."""
        self.cache = {}

    def get_key(self, text: str, target_lang: str) -> str:
        """Generate cache key for text and language."""
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()[:10]
        return f"{target_lang}_{text_hash}"

    def get(self, text: str, target_lang: str) -> Optional[str]:
        """Get cached translation if available."""
        key = self.get_key(text, target_lang)
        return self.cache.get(key)

    def set(self, text: str, target_lang: str, translation: str):
        """Cache a translation."""
        key = self.get_key(text, target_lang)
        self.cache[key] = translation

    def clear(self):
        """Clear all cached translations."""
        self.cache.clear()


class TranslatorWithCache(MultiTranslator):
    """Translator with built-in caching support."""

    def __init__(self, *args, **kwargs):
        """Initialize translator with cache."""
        super().__init__(*args, **kwargs)
        self.cache = TranslationCache()

    def translate_text(self, text: str, target_lang: str) -> str:
        """Translate text with caching."""
        # Check cache first
        cached = self.cache.get(text, target_lang)
        if cached:
            logger.debug(f"Using cached translation for {target_lang}")
            return cached

        # Translate and cache
        translated = super().translate_text(text, target_lang)
        if translated != text:  # Only cache successful translations
            self.cache.set(text, target_lang, translated)

        return translated


def test_translator():
    """Test translator with sample text."""
    text = "Hello, this is a test of the translation system."

    # Test with different providers
    for provider in ['google', 'mymemory']:
        try:
            print(f"\nTesting {provider} provider:")
            translator = MultiTranslator(
                target_languages=['ko', 'ja', 'zh-CN'],
                provider=provider
            )

            for lang in ['ko', 'ja', 'zh-CN']:
                translated = translator.translate_text(text, lang)
                print(f"  {lang}: {translated}")

        except Exception as e:
            print(f"  Failed: {e}")

    # Test with cache
    print("\nTesting with cache:")
    cached_translator = TranslatorWithCache(['ko'], provider='google')

    # First call - no cache
    start = time.time()
    result1 = cached_translator.translate_text(text, 'ko')
    time1 = time.time() - start
    print(f"  First call ({time1:.2f}s): {result1}")

    # Second call - from cache
    start = time.time()
    result2 = cached_translator.translate_text(text, 'ko')
    time2 = time.time() - start
    print(f"  Second call ({time2:.2f}s): {result2}")
    print(f"  Cache speedup: {time1/max(time2, 0.001):.1f}x")
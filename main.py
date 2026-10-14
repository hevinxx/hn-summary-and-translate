#!/usr/bin/env python3
"""Main orchestrator for HN RSS Translator."""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Import our modules
from src.fetcher import RSSFetcher
from src.scraper import batch_scrape
from src.summarizer import Summarizer, LightweightSummarizer
from src.translator import TranslatorWithCache
from src.generator import MultiLanguageRSSGenerator, generate_index_page, generate_sitemap, generate_robots_txt
from src.utils import (
    CacheManager,
    ModelCache,
    setup_logging,
    load_config,
    deduplicate_items,
    ensure_directories,
    clean_text_for_processing,
    calculate_processing_stats,
    print_processing_summary,
    RateLimiter
)

logger = logging.getLogger(__name__)


class HNRSSTranslator:
    """Main orchestrator for the HN RSS translation pipeline."""

    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialize the translator.

        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.cache_manager = CacheManager(
            cache_dir='cache',
            ttl_days=self.config['output']['keep_days']
        )
        self.model_cache = ModelCache(cache_dir='cache')
        self.rate_limiter = RateLimiter(calls_per_second=2.0)

        # Initialize components (lazy loading)
        self.fetcher = None
        self.summarizer = None
        self.translator = None
        self.rss_generator = None

        # Statistics
        self.stats = {
            'items_fetched': 0,
            'items_scraped': 0,
            'items_summarized': 0,
            'items_translated': 0,
            'items_generated': 0
        }

    def initialize_components(self):
        """Initialize all components."""
        logger.info("Initializing components...")

        # RSS Fetcher
        self.fetcher = RSSFetcher(self.config['general']['source_feed'])

        # Summarizer (with fallback)
        try:
            self.summarizer = Summarizer(
                model_name=self.config['summarization']['model'],
                max_length=self.config['summarization']['max_length'],
                min_length=self.config['summarization']['min_length']
            )
        except Exception as e:
            logger.error(f"Failed to initialize transformer summarizer: {e}")
            logger.info("Using lightweight summarizer as fallback")
            self.summarizer = LightweightSummarizer(max_sentences=3)

        # Translator
        # Only include languages that need translation (skip those with skip_translation=true)
        target_languages = [
            lang['code']
            for lang in self.config['translation']['target_languages']
            if not lang.get('skip_translation', False)
        ]
        self.translator = TranslatorWithCache(
            target_languages=target_languages,
            provider=self.config['translation']['provider']
        )

        # RSS Generator
        self.rss_generator = MultiLanguageRSSGenerator(
            base_url=self.config['output']['base_url'],
            languages=self.config['translation']['target_languages']
        )

        logger.info("Components initialized successfully")

    def run(self):
        """Run the complete translation pipeline."""
        start_time = datetime.now()
        logger.info("=" * 50)
        logger.info("Starting HN RSS Translator")
        logger.info("=" * 50)

        try:
            # Ensure directories exist
            ensure_directories('cache', 'output')

            # Initialize components
            self.initialize_components()

            # Step 1: Fetch RSS feed
            logger.info("📡 Fetching RSS feed...")
            items = self.fetcher.fetch_feed(
                max_age_hours=self.config['filtering']['max_age_hours'],
                max_items=self.config['filtering']['max_items'],
                skip_jobs=self.config['filtering']['skip_jobs']
            )
            self.stats['items_fetched'] = len(items)
            logger.info(f"Fetched {len(items)} items from RSS feed")

            if not items:
                logger.warning("No items to process")
                return

            # Step 2: Deduplicate against cache
            logger.info("🔍 Checking for duplicates...")
            new_items = deduplicate_items(items, self.cache_manager.cache)
            logger.info(f"Found {len(new_items)} new items to process")

            # Step 3: Process items or use cached items
            if new_items:
                # Step 3a: Scrape web content for new items
                logger.info("🌐 Scraping web content...")
                urls = [item['link'] for item in new_items]
                content_map = batch_scrape(urls, max_workers=5)
                self.stats['items_scraped'] = sum(1 for v in content_map.values() if v)
                logger.info(f"Successfully scraped {self.stats['items_scraped']} pages")

                # Step 4a: Process new items (summarize and translate)
                logger.info("🤖 Processing items...")
                processed_items = self._process_items(new_items, content_map)
                self.stats['items_generated'] = len(processed_items)
            else:
                # Step 3b: No new items, use cached items for RSS generation
                logger.info("No new items found, using cached items for RSS generation")
                processed_items = self._get_cached_items()
                logger.info(f"Retrieved {len(processed_items)} items from cache")
                self.stats['items_generated'] = len(processed_items)

            # Step 5: Generate RSS feeds
            logger.info("📝 Generating RSS feeds...")
            items_by_language = self._organize_items_by_language(processed_items)
            feeds = self.rss_generator.generate_all_feeds(items_by_language)

            # Step 6: Save feeds
            logger.info("💾 Saving RSS feeds...")
            self.rss_generator.save_all_feeds(feeds, 'output')

            # Step 7: Generate index page
            if self.config['output']['generate_index']:
                generate_index_page(
                    self.config['output']['base_url'],
                    self.config['translation']['target_languages'],
                    'output'
                )

            # Step 8: Generate SEO files (sitemap and robots.txt)
            logger.info("🔍 Generating SEO files...")
            generate_sitemap(
                self.config['output']['base_url'],
                self.config['translation']['target_languages'],
                'output'
            )
            generate_robots_txt(
                self.config['output']['base_url'],
                'output'
            )

            # Step 9: Save cache
            logger.info("💾 Saving cache...")
            self.cache_manager.save_cache()

            # Print summary
            stats = calculate_processing_stats(
                start_time,
                self.stats['items_generated'],
                len(new_items) - self.stats['items_generated']
            )
            print_processing_summary(stats)
            self._report_translation_failures()

            logger.info("✅ Translation pipeline completed successfully!")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise

    def _process_items(self, items: List[Dict], content_map: Dict[str, str]) -> List[Dict]:
        """
        Process items through summarization and translation.

        Args:
            items: List of RSS items
            content_map: Mapping of URLs to scraped content

        Returns:
            List of processed items
        """
        processed_items = []

        for i, item in enumerate(items, 1):
            try:
                logger.debug(f"Processing item {i}/{len(items)}: {item['title'][:50]}...")

                # Get content (scraped only - HN RSS description is just "Comments" link)
                content = content_map.get(item['link'])
                if not content:
                    logger.warning(f"No scraped content for {item['link'][:50]}..., using empty summary")
                    summary = ""
                else:
                    # Clean content for processing
                    content = clean_text_for_processing(content)

                    # Summarize
                    if not content:
                        logger.warning(f"Empty content after cleaning for {item['title'][:50]}..., using empty summary")
                        summary = ""
                    else:
                        # Check cache first
                        summary = self.model_cache.get_summary(content)
                        if not summary:
                            if isinstance(self.summarizer, Summarizer):
                                summary = self.summarizer.summarize(content)
                            else:
                                summary = self.summarizer.summarize(content)
                            self.model_cache.set_summary(content, summary)
                            self.stats['items_summarized'] += 1

                        if not summary:
                            logger.warning(f"Failed to generate summary for {item['title'][:50]}..., using empty summary")
                            summary = ""

                # Translate
                translations = {}
                translation_failed = False
                for lang_config in self.config['translation']['target_languages']:
                    lang_code = lang_config['code']
                    skip_translation = lang_config.get('skip_translation', False)

                    # Skip translation for specified languages (e.g., English)
                    if skip_translation:
                        translations[lang_code] = {
                            'title': item['title'],
                            'description': summary
                        }
                        logger.debug(f"Skipping translation for {lang_config['name']} (using original)")
                    else:
                        # Check cache first (entries equal to the original are failed
                        # translations cached by earlier versions, so treat them as misses)
                        cached_title = self.model_cache.get_translation(item['title'], lang_code)
                        cached_summary = self.model_cache.get_translation(summary, lang_code)

                        if (cached_title and cached_title != item['title']
                                and cached_summary and cached_summary != summary):
                            translations[lang_code] = {
                                'title': cached_title,
                                'description': cached_summary
                            }
                        else:
                            # Translate with rate limiting
                            self.rate_limiter.wait()
                            failures_before = self.translator.failure_count
                            translated_title = self.translator.translate_text(item['title'], lang_code)
                            translated_summary = self.translator.translate_text(summary, lang_code)

                            translations[lang_code] = {
                                'title': translated_title,
                                'description': translated_summary
                            }

                            if self.translator.failure_count > failures_before:
                                translation_failed = True

                            # Cache only actual translations so failures are retried next run
                            if translated_title != item['title']:
                                self.model_cache.set_translation(item['title'], lang_code, translated_title)
                            if translated_summary != summary:
                                self.model_cache.set_translation(summary, lang_code, translated_summary)
                            self.stats['items_translated'] += 1

                # Store processed item
                processed_item = {
                    **item,
                    'summary': summary,
                    'translations': translations,
                    'original_title': item['title'],
                    'processed_at': datetime.now().isoformat()
                }

                processed_items.append(processed_item)

                # Update cache (skip items with failed translations so they are retried next run)
                if translation_failed:
                    logger.warning(f"Translation failed for {item['title'][:50]}..., not caching item")
                else:
                    self.cache_manager.set(item['guid'], processed_item)

            except Exception as e:
                logger.error(f"Failed to process item {item.get('title', 'Unknown')}: {e}")
                continue

        return processed_items

    def _report_translation_failures(self):
        """Warn when every translation request failed; the feeds are still published."""
        attempts = self.translator.attempt_count
        failures = self.translator.failure_count
        if attempts == 0:
            return

        logger.info(f"Translation requests: {attempts - failures}/{attempts} succeeded")
        if failures == attempts:
            message = (f"All {attempts} translation requests failed; "
                       "feeds were published with untranslated text")
            logger.warning(message)
            if os.environ.get('GITHUB_ACTIONS') == 'true':
                # Shows up as an annotation on the workflow run summary
                print(f"::warning title=Translation failed::{message}")

    def _get_cached_items(self) -> List[Dict]:
        """
        Get recent items from cache for RSS generation.

        Returns:
            List of cached processed items, sorted by processed_at (newest first)
        """
        cached_items = []

        for key, value in self.cache_manager.cache.items():
            if isinstance(value, dict) and 'translations' in value:
                cached_items.append(value)

        # Sort by processed_at (newest first)
        cached_items.sort(
            key=lambda x: x.get('processed_at', ''),
            reverse=True
        )

        # Limit to max_items from config
        max_items = self.config['filtering']['max_items']
        return cached_items[:max_items]

    def _organize_items_by_language(self, items: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Organize items by language for feed generation.

        Args:
            items: List of processed items

        Returns:
            Dictionary mapping language codes to items
        """
        items_by_language = {}

        for lang_config in self.config['translation']['target_languages']:
            lang_code = lang_config['code']
            lang_items = []

            for item in items:
                if lang_code in item.get('translations', {}):
                    translation = item['translations'][lang_code]
                    lang_item = {
                        'title': translation['title'],
                        'description': translation['description'],
                        'link': item['link'],
                        'guid': item['guid'],
                        'published': item['published'],
                        'comments': item.get('comments'),
                        'author': item.get('author'),
                        'score': item.get('score'),
                        'original_title': item.get('original_title')
                    }
                    lang_items.append(lang_item)

            items_by_language[lang_code] = lang_items

        return items_by_language


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='HN RSS Translator')
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode with limited items'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Modify config for test mode
    if args.test:
        logger.info("Running in test mode")
        # Override some settings for testing
        import yaml
        config = load_config(args.config)
        config['filtering']['max_items'] = 3
        with open('config_test.yaml', 'w') as f:
            yaml.dump(config, f)
        args.config = 'config_test.yaml'

    try:
        # Run the translator
        translator = HNRSSTranslator(args.config)
        translator.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
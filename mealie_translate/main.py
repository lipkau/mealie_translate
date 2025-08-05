#!/usr/bin/env python3
"""Main script for the Mealie Recipe Translator."""

import argparse

from .config import get_settings
from .logger import get_logger
from .recipe_processor import RecipeProcessor


def main():
    """Main application entry point."""
    logger = get_logger(__name__)

    parser = argparse.ArgumentParser(
        description="Translate Mealie recipes using ChatGPT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Process all unprocessed recipes
  python main.py --recipe my-recipe-slug   # Process a specific recipe
  python main.py --dry-run                 # Show what would be processed
        """,
    )

    parser.add_argument("--recipe", type=str, help="Process a specific recipe by slug")

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without making changes",
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to .env file (default: .env in current directory)",
    )

    args = parser.parse_args()

    # Load configuration
    try:
        settings = get_settings()

        # Validate required settings
        if not settings.mealie_base_url:
            logger.error("Error: MEALIE_BASE_URL not configured")
            return 1

        if not settings.openai_api_key:
            logger.error("Error: OPENAI_API_KEY not configured")
            return 1

        if not settings.mealie_api_token:
            logger.error("Error: MEALIE_API_TOKEN not configured")
            return 1

        logger.info("Configuration loaded successfully")

        # Initialize processor
        processor = RecipeProcessor(settings)

        # Process recipes
        if args.recipe:
            # Process specific recipe
            logger.info(f"Processing specific recipe: {args.recipe}")
            if args.dry_run:
                logger.info("DRY RUN: Would process recipe - no changes will be made")
                return 0

            result = processor.process_single_recipe(args.recipe)
            if result:
                logger.info(f"Successfully processed recipe: {args.recipe}")
            else:
                logger.error(f"Failed to process recipe: {args.recipe}")
                return 1
        else:
            # Process all unprocessed recipes
            logger.info("Starting to process all unprocessed recipes")
            if args.dry_run:
                logger.info(
                    "DRY RUN: Would process all recipes - no changes will be made"
                )
                return 0

            results = processor.process_all_recipes()

            logger.info(f"Processing complete. Results: {results}")

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())

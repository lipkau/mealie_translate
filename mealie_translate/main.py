#!/usr/bin/env python3
"""Main script for the Mealie Recipe Translator."""

import argparse

from .config import get_settings
from .logger import get_logger, setup_logging
from .organizer import RecipeOrganizer
from .recipe_processor import RecipeProcessor


def main():
    """Main application entry point."""
    setup_logging()
    logger = get_logger(__name__)

    parser = argparse.ArgumentParser(
        description="Translate Mealie recipes using ChatGPT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                         # Translate + organise all recipes
  python main.py --recipe my-recipe-slug # Translate + organise a specific recipe
  python main.py --skip-organise         # Translate only, skip tag/category generation
        """,
    )

    parser.add_argument("--recipe", type=str, help="Process a specific recipe by slug")

    parser.add_argument(
        "--config",
        type=str,
        help="Path to .env file (default: .env in current directory)",
    )

    parser.add_argument(
        "--skip-organise",
        action="store_true",
        help="Skip tag and category generation after translation",
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

        processor = RecipeProcessor(settings)
        organizer = RecipeOrganizer(settings=settings)

        if args.recipe:
            # Translate the specific recipe
            logger.info(f"Processing specific recipe: {args.recipe}")
            result = processor.process_single_recipe(args.recipe)
            if not result:
                logger.error(f"Failed to process recipe: {args.recipe}")
                return 1
            logger.info(f"Successfully translated recipe: {args.recipe}")

            # Organise the same recipe unless skipped
            if not args.skip_organise:
                logger.info(f"Organising recipe: {args.recipe}")
                organizer.process_recipe(args.recipe)
        else:
            # Translate all unprocessed recipes
            logger.info("Starting to translate all unprocessed recipes")
            results = processor.process_all_recipes()
            logger.info(f"Translation complete. Results: {results}")

            # Organise all recipes (including already-translated ones)
            if not args.skip_organise:
                logger.info("Starting to organise all recipes (tags + categories)")
                org_results = organizer.process_all_recipes()
                logger.info(f"Organisation complete. Results: {org_results}")

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())

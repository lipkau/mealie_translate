#!/usr/bin/env python3
"""Main script for the Mealie Recipe Translator."""

import argparse
import asyncio

from .config import get_settings
from .logger import get_logger, setup_logging
from .organizer import RecipeOrganizer
from .recipe_processor import RecipeProcessor


async def async_main() -> int:
    """Async main application entry point."""
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

    try:
        settings = get_settings()

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

        if args.recipe:
            async with RecipeProcessor(settings) as processor:
                logger.info(f"Processing specific recipe: {args.recipe}")
                result = await processor.process_single_recipe(args.recipe)
                if not result:
                    logger.error(f"Failed to process recipe: {args.recipe}")
                    return 1
                logger.info(f"Successfully translated recipe: {args.recipe}")

            if not args.skip_organise:
                async with RecipeOrganizer(settings=settings) as organizer:
                    logger.info(f"Organising recipe: {args.recipe}")
                    await organizer.process_recipe(args.recipe)
        else:
            async with RecipeProcessor(settings) as processor:
                logger.info("Starting to translate all unprocessed recipes")
                results = await processor.process_all_recipes()
                logger.info(f"Translation complete. Results: {results}")

            if not args.skip_organise:
                async with RecipeOrganizer(settings=settings) as organizer:
                    logger.info("Starting to organise all recipes (tags + categories)")
                    org_results = await organizer.process_all_recipes()
                    logger.info(f"Organisation complete. Results: {org_results}")

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        return 1

    return 0


def main() -> int:
    """Main entry point that runs the async main function."""
    return asyncio.run(async_main())


if __name__ == "__main__":
    import sys

    sys.exit(main())

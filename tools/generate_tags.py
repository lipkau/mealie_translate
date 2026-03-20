#!/usr/bin/env python3
"""CLI tool for generating tags and categories for Mealie recipes.

This is a thin wrapper around mealie_translate.organizer.RecipeOrganizer.
Run it standalone for ad-hoc use; the Docker app calls the organizer
automatically as part of its periodic cron job.
"""

import argparse
import sys
from pathlib import Path

# Add the package to the Python path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from mealie_translate.config import get_settings
from mealie_translate.logger import get_logger
from mealie_translate.organizer import RecipeOrganizer


def main() -> int:
    """CLI entry point."""
    logger = get_logger(__name__)

    parser = argparse.ArgumentParser(
        description="Generate tags and categories for Mealie recipes using LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/generate_tags.py                              # Organise all recipes (tags + categories)
  python tools/generate_tags.py --recipe my-recipe-slug     # Organise one recipe
  python tools/generate_tags.py --tags-only                  # Only generate tags
  python tools/generate_tags.py --categories-only            # Only generate categories
  python tools/generate_tags.py --dry-run                    # Preview without changes
        """,
    )
    parser.add_argument("--recipe", type=str, help="Process a specific recipe by slug")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview generated tags/categories without making any changes",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--tags-only",
        action="store_true",
        help="Generate tags only (skip category generation)",
    )
    mode_group.add_argument(
        "--categories-only",
        action="store_true",
        help="Generate categories only (skip tag generation)",
    )
    args = parser.parse_args()

    try:
        settings = get_settings()

        if not settings.mealie_base_url:
            logger.error("MEALIE_BASE_URL not configured")
            return 1
        if not settings.openai_api_key:
            logger.error("OPENAI_API_KEY not configured")
            return 1
        if not settings.mealie_api_token:
            logger.error("MEALIE_API_TOKEN not configured")
            return 1

        if args.dry_run:
            logger.info("DRY RUN mode enabled — no changes will be made")

        generate_tags = not args.categories_only
        generate_categories = not args.tags_only

        organizer = RecipeOrganizer(settings=settings, dry_run=args.dry_run)

        if args.recipe:
            success = organizer.process_recipe(
                args.recipe,
                generate_tags=generate_tags,
                generate_categories=generate_categories,
            )
            return 0 if success else 1

        stats = organizer.process_all_recipes(
            generate_tags=generate_tags,
            generate_categories=generate_categories,
            skip_organised=False,  # CLI always re-processes; app uses the default (True)
        )
        logger.info(
            f"Done! total={stats['total']} updated={stats['updated']} "
            f"skipped={stats['skipped']} failed={stats['failed']}"
        )
        return 0 if stats["failed"] == 0 else 1

    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

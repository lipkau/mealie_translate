"""Utilities for displaying diffs in dry run mode."""

from typing import Any

from .logger import get_logger

logger = get_logger(__name__)


class DiffFormatter:
    """Formats before/after diffs for recipes in a readable way."""

    # Box drawing characters for nice formatting
    TOP_LEFT = "┌"
    TOP_RIGHT = "┐"
    BOTTOM_LEFT = "└"
    BOTTOM_RIGHT = "┘"
    HORIZONTAL = "─"
    VERTICAL = "│"

    @classmethod
    def format_recipe_diff(
        cls, recipe_name: str, original: dict[str, Any], translated: dict[str, Any]
    ) -> str:
        """Format a complete recipe diff for display."""
        lines = []
        lines.append(f"[DRY RUN] Recipe: {recipe_name}")

        # Compare each field that might have changed
        fields_to_compare = [
            ("name", "Title"),
            ("description", "Description"),
            ("recipeInstructions", "Instructions"),
            ("recipeIngredient", "Ingredients"),
        ]

        for field_key, field_name in fields_to_compare:
            diff = cls._format_field_diff(
                field_name, original.get(field_key), translated.get(field_key)
            )
            if diff:
                lines.append(diff)

        return "\n".join(lines)

    @classmethod
    def _format_field_diff(
        cls, field_name: str, original: Any, translated: Any
    ) -> str | None:
        """Format a diff for a specific field."""
        if original == translated:
            return None  # No changes

        lines = []

        # Create the header box
        header = f" {field_name} "
        box_width = max(50, len(header) + 4)
        padding = cls.HORIZONTAL * (box_width - len(header) - 2)

        lines.append(
            f"{cls.TOP_LEFT}{cls.HORIZONTAL} {field_name} {padding}{cls.TOP_RIGHT}"
        )

        # Handle different field types
        if isinstance(original, list) and isinstance(translated, list):
            # Handle ingredient/instruction lists
            lines.extend(cls._format_list_diff(original, translated, box_width))
        else:
            # Handle string fields (title, description)
            lines.extend(
                cls._format_text_diff(
                    str(original or ""), str(translated or ""), box_width
                )
            )

        lines.append(f"{cls.BOTTOM_LEFT}{'─' * (box_width - 2)}{cls.BOTTOM_RIGHT}")

        return "\n".join(lines)

    @classmethod
    def _format_text_diff(
        cls, original: str, translated: str, box_width: int
    ) -> list[str]:
        """Format diff for text fields."""
        lines = []

        # For long text, show first difference or truncate
        orig_lines = original.split("\n")[:3]  # Show max 3 lines
        trans_lines = translated.split("\n")[:3]

        max_lines = max(len(orig_lines), len(trans_lines))

        for i in range(max_lines):
            orig_line = orig_lines[i] if i < len(orig_lines) else ""
            trans_line = trans_lines[i] if i < len(trans_lines) else ""

            if orig_line:
                truncated = (
                    orig_line[: box_width - 6] + "..."
                    if len(orig_line) > box_width - 6
                    else orig_line
                )
                lines.append(
                    f"{cls.VERTICAL} - {truncated:<{box_width - 6}} {cls.VERTICAL}"
                )

            if trans_line:
                truncated = (
                    trans_line[: box_width - 6] + "..."
                    if len(trans_line) > box_width - 6
                    else trans_line
                )
                lines.append(
                    f"{cls.VERTICAL} + {truncated:<{box_width - 6}} {cls.VERTICAL}"
                )

        return lines

    @classmethod
    def _format_list_diff(
        cls, original: list, translated: list, box_width: int
    ) -> list[str]:
        """Format diff for list fields (ingredients/instructions)."""
        lines = []

        # Show first few items that are different
        max_items = min(3, max(len(original), len(translated)))

        for i in range(max_items):
            orig_item = original[i] if i < len(original) else None
            trans_item = translated[i] if i < len(translated) else None

            if orig_item:
                # For ingredients, show the note/originalText, for instructions show text
                orig_text = orig_item.get(
                    "note",
                    orig_item.get(
                        "originalText", orig_item.get("text", str(orig_item))
                    ),
                )
                truncated = (
                    orig_text[: box_width - 6] + "..."
                    if len(orig_text) > box_width - 6
                    else orig_text
                )
                lines.append(
                    f"{cls.VERTICAL} - {truncated:<{box_width - 6}} {cls.VERTICAL}"
                )

            if trans_item:
                trans_text = trans_item.get(
                    "note",
                    trans_item.get(
                        "originalText", trans_item.get("text", str(trans_item))
                    ),
                )
                truncated = (
                    trans_text[: box_width - 6] + "..."
                    if len(trans_text) > box_width - 6
                    else trans_text
                )
                lines.append(
                    f"{cls.VERTICAL} + {truncated:<{box_width - 6}} {cls.VERTICAL}"
                )

        # Show count if lists have different lengths
        if len(original) != len(translated):
            count_line = f"({len(original)} → {len(translated)} items)"
            lines.append(f"{cls.VERTICAL} {count_line:<{box_width - 4}} {cls.VERTICAL}")

        return lines


def log_dry_run_diff(
    recipe_name: str, original: dict[str, Any], translated: dict[str, Any]
) -> None:
    """Log a formatted diff for a recipe in dry run mode."""
    diff_output = DiffFormatter.format_recipe_diff(recipe_name, original, translated)

    # Log each line separately to avoid formatting issues
    for line in diff_output.split("\n"):
        logger.info(line)

    # Add separator
    logger.info("=" * 60)


def has_changes(original: dict[str, Any], translated: dict[str, Any]) -> bool:
    """Check if there are any actual changes between original and translated recipe."""
    fields_to_check = [
        "name",
        "description",
        "recipeInstructions",
        "recipeIngredient",
    ]

    for field in fields_to_check:
        if original.get(field) != translated.get(field):
            return True

    return False

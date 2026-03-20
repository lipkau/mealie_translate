"""Recipe organiser: LLM-powered tag and category generation for Mealie.

Tags describe WHAT a recipe is (cuisine, ingredient, method, flavor, etc.).
Categories describe WHEN/WHERE it fits in a meal (breakfast, dinner, dessert, etc.).

Both are generated in a single pass per recipe and persisted with one API call.
"""

from abc import ABC, abstractmethod
from typing import Any

from .config import Settings, get_settings
from .logger import get_logger
from .mealie_client import MealieClient
from .translator import RecipeTranslator

# ── Taxonomy constants ─────────────────────────────────────────────────────

# Controlled vocabulary for categories — must match docs/TAXONOMY.md exactly.
ALLOWED_CATEGORIES: frozenset[str] = frozenset(
    {
        "breakfast",
        "brunch",
        "lunch",
        "dinner",
        "snack",
        "dessert",
        "appetizer",
        "side",
        "drink",
        "condiment",
        "bread",
        "baked-goods",
    }
)

# extras key used to mark a recipe as organised — same pattern as extras.translated.
EXTRAS_ORGANISED_KEY: str = "organised"

# ── LLM prompts ────────────────────────────────────────────────────────────

TAG_GENERATION_PROMPT = """You are a recipe tagging expert. Analyze the following recipe and generate 3-8 relevant tags.

TAXONOMY RULES — follow these exactly:

1. Tags describe WHAT a recipe is, not WHEN it is eaten.
   Meal-position words (breakfast, lunch, dinner, snack, dessert, appetizer, side, drink, condiment, bread, baked-goods)
   belong in CATEGORIES only — never emit them as tags.

2. Draw tags from these semantic dimensions (pick the most relevant ones):
   - Cuisine/Origin:    brazilian, italian, french, german, japanese, chinese, mexican, portuguese, american, indian, greek
   - Main ingredient:   chicken, beef, pork, fish, seafood, egg, cheese, pasta, rice, potato, bean, lentil, mushroom, tomato
   - Dietary:          vegetarian, vegan, gluten-free, dairy-free, nut-free, low-carb, keto, paleo
   - Cooking method:   baked, fried, grilled, steamed, slow-cooked, no-cook, one-pot, air-fryer, roasted, stir-fried
   - Flavor profile:   sweet, savory, spicy, creamy, smoky, tangy, citrusy, hearty, light
   - Effort/Time:      quick (≤30 min), make-ahead, meal-prep, weeknight, weekend-project
   - Specific dish:    pao-de-queijo, lasagna, brigadeiro, feijoada, carbonara, bolognese, risotto, paella, hummus, tiramisu

3. All tags are lowercase. Multi-word tags use hyphens (e.g. gluten-free, pao-de-queijo).

4. Specific-dish tags supplement dimensional tags, not replace them.
   Example: pao-de-queijo should also have brazilian, cheese, gluten-free, baked.

5. PREFER reusing tags from the "Available Tags" catalog below over inventing new ones.

6. Do NOT duplicate tags already on the recipe (listed under "Recipe's Current Tags").

Available Tags (reuse these when applicable): {available_tags}

Recipe Name: {name}
Description: {description}
Ingredients: {ingredients}
Current Categories: {existing_categories}
Recipe's Current Tags: {existing_tags}

Return ONLY a comma-separated list of new tags to add, nothing else.
Example output: brazilian, cheese, gluten-free, baked, quick"""

CATEGORY_GENERATION_PROMPT = """You are a recipe categorisation expert. Assign the correct meal-position category (or categories) to the following recipe.

ALLOWED CATEGORIES — use ONLY these exact values:
  breakfast   — morning meals (sweet or savoury)
  brunch      — late-morning meals combining breakfast and lunch elements
  lunch       — midday meals
  dinner      — main evening dish (use instead of the legacy value "main")
  snack       — small bites eaten between main meals
  dessert     — sweet dishes served after a meal or as a treat
  appetizer   — starters served before a main course
  side        — accompaniments served alongside a main dish
  drink       — beverages, smoothies, juices, cocktails
  condiment   — sauces, dips, dressings, spreads
  bread       — breads, rolls, savoury baked goods (non-dessert)
  baked-goods — sweet baked goods that are not clearly a dessert (e.g. muffins for breakfast)

RULES:
1. Only output values from the allowed list above — nothing else.
2. A recipe may belong to multiple categories (e.g. pao-de-queijo → snack, breakfast, bread).
3. Do NOT repeat categories already assigned (listed under "Recipe's Current Categories").
4. "main" is NOT valid — use "dinner" instead.
5. All values are lowercase and hyphenated where multi-word.

Recipe Name: {name}
Description: {description}
Ingredients: {ingredients}
Recipe's Current Tags: {existing_tags}
Recipe's Current Categories: {existing_categories}

Return ONLY a comma-separated list of new categories to add, nothing else.
Example output: snack, breakfast"""

# ── Shared recipe-summary helper ───────────────────────────────────────────


def _build_recipe_summary(recipe: dict[str, Any]) -> dict[str, str]:
    """Extract text fields common to all LLM prompts from a recipe dict."""
    name = recipe.get("name", "") or ""
    description = (recipe.get("description", "") or "")[:500]

    ingredients: list[str] = []
    for ing in recipe.get("recipeIngredient", []) or []:
        food = ing.get("food") or {}
        if food.get("name"):
            ingredients.append(food["name"])
        elif ing.get("note"):
            ingredients.append(ing["note"])
        elif ing.get("originalText"):
            ingredients.append(ing["originalText"])

    existing_categories = [
        c["name"] for c in (recipe.get("recipeCategory", []) or []) if c.get("name")
    ]
    existing_tags = [t["name"] for t in (recipe.get("tags", []) or []) if t.get("name")]

    return {
        "name": name,
        "description": description or "N/A",
        "ingredients": ", ".join(ingredients[:20]) if ingredients else "N/A",
        "existing_categories": ", ".join(existing_categories)
        if existing_categories
        else "None",
        "existing_tags": ", ".join(existing_tags) if existing_tags else "None",
    }


# ── Abstract base for organiser generators ─────────────────────────────────


class OrganizerGenerator(ABC):
    """Base class for LLM-powered Mealie organiser generators (tags, categories).

    Subclasses declare their Mealie API path, recipe field name, and LLM prompt
    logic. All Mealie CRUD and the apply-to-recipe workflow are inherited.
    """

    def __init__(
        self,
        mealie_client: MealieClient,
        translator: RecipeTranslator,
        dry_run: bool = False,
    ) -> None:
        """Initialise the generator with shared Mealie client and translator."""
        self.mealie_client = mealie_client
        self.translator = translator
        self.dry_run = dry_run
        self.logger = get_logger(__name__)
        self._cache: dict[str, dict[str, Any]] = {}

    # ── Subclass contract ──────────────────────────────────────────────────

    @property
    @abstractmethod
    def organizer_name(self) -> str:
        """Singular human-readable name, e.g. 'tag' or 'category'."""

    @property
    @abstractmethod
    def api_path(self) -> str:
        """Mealie API sub-path, e.g. 'organizers/tags'."""

    @property
    @abstractmethod
    def recipe_field(self) -> str:
        """Key in the recipe dict, e.g. 'tags' or 'recipeCategory'."""

    @abstractmethod
    def _generate_names(self, recipe: dict[str, Any]) -> list[str]:
        """Call the LLM and return a list of organiser names to add."""

    # ── Mealie API helpers ─────────────────────────────────────────────────

    def _api_url(self) -> str:
        return f"{self.mealie_client.base_url}/api/{self.api_path}"

    def load_existing(self) -> dict[str, dict[str, Any]]:
        """Fetch all organisers of this type from Mealie (result is cached)."""
        if self._cache:
            return self._cache

        page, per_page = 1, 100
        while True:
            response = self.mealie_client.session.get(
                self._api_url(),
                params={"page": page, "perPage": per_page},
                timeout=30,
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            items: list[dict[str, Any]] = data.get("items", [])
            for item in items:
                item_name = item.get("name", "")
                if item_name:
                    self._cache[item_name.lower()] = item
            if len(items) < per_page:
                break
            page += 1

        self.logger.debug(
            f"Loaded {len(self._cache)} existing {self.organizer_name}s from Mealie"
        )
        return self._cache

    def get_or_create(self, name: str) -> dict[str, Any] | None:
        """Return an existing organiser object, creating it if it doesn't exist."""
        existing = self.load_existing()
        key = name.lower().strip()

        if key in existing:
            return existing[key]

        if self.dry_run:
            self.logger.info(
                f"[DRY RUN] Would create new {self.organizer_name}: '{name}'"
            )
            return {"name": name}

        try:
            response = self.mealie_client.session.post(
                self._api_url(),
                json={"name": name},
                timeout=30,
            )
            response.raise_for_status()
            new_item: dict[str, Any] = response.json()
            self._cache[key] = new_item
            self.logger.info(f"Created new {self.organizer_name}: '{name}'")
            return new_item
        except Exception as e:
            self.logger.error(f"Failed to create {self.organizer_name} '{name}': {e}")
            return None

    # ── Per-recipe workflow ────────────────────────────────────────────────

    def apply_to_recipe(self, recipe: dict[str, Any]) -> bool:
        """Generate and merge new organisers into *recipe* in-place.

        The caller is responsible for persisting the updated recipe to Mealie.

        Returns:
            True on success (even when nothing new was added).
        """
        recipe_name = recipe.get("name", "unknown")
        generated = self._generate_names(recipe)

        if not generated:
            self.logger.warning(
                f"No {self.organizer_name}s generated for: {recipe_name}"
            )
            return True

        self.logger.debug(
            f"Generated {self.organizer_name} suggestions for '{recipe_name}': {generated}"
        )

        existing_names = {
            item["name"].lower()
            for item in (recipe.get(self.recipe_field, []) or [])
            if item.get("name")
        }
        new_names = [n for n in generated if n not in existing_names]

        if not new_names:
            self.logger.info(
                f"All generated {self.organizer_name}s already present on '{recipe_name}'"
            )
            return True

        if self.dry_run:
            self.logger.info(
                f"[DRY RUN] Would add {self.organizer_name}s {new_names} to '{recipe_name}'"
            )
            return True

        new_objects: list[dict[str, Any]] = []
        for name in new_names:
            obj = self.get_or_create(name)
            if obj:
                new_objects.append(obj)

        if not new_objects:
            self.logger.warning(
                f"No valid {self.organizer_name} objects to add to '{recipe_name}'"
            )
            return False

        recipe[self.recipe_field] = (recipe.get(self.recipe_field) or []) + new_objects
        added = [o["name"] for o in new_objects]
        self.logger.info(f"Staged {self.organizer_name}s {added} for '{recipe_name}'")
        return True


# ── Concrete generators ────────────────────────────────────────────────────


class TagGenerator(OrganizerGenerator):
    """Generates free-form, dimensional tags for a recipe."""

    @property
    def organizer_name(self) -> str:
        return "tag"

    @property
    def api_path(self) -> str:
        return "organizers/tags"

    @property
    def recipe_field(self) -> str:
        return "tags"

    def _generate_names(self, recipe: dict[str, Any]) -> list[str]:
        summary = _build_recipe_summary(recipe)
        all_tags = sorted(self.load_existing().keys())
        summary["available_tags"] = ", ".join(all_tags) if all_tags else "None"
        raw = self.translator._call_openai(TAG_GENERATION_PROMPT.format(**summary))
        if not raw:
            return []
        return [t.strip().lower() for t in raw.split(",") if t.strip()]


class CategoryGenerator(OrganizerGenerator):
    """Generates controlled-vocabulary categories for a recipe."""

    @property
    def organizer_name(self) -> str:
        return "category"

    @property
    def api_path(self) -> str:
        return "organizers/categories"

    @property
    def recipe_field(self) -> str:
        return "recipeCategory"

    def _generate_names(self, recipe: dict[str, Any]) -> list[str]:
        summary = _build_recipe_summary(recipe)
        raw = self.translator._call_openai(CATEGORY_GENERATION_PROMPT.format(**summary))
        if not raw:
            return []
        candidates = [c.strip().lower() for c in raw.split(",") if c.strip()]
        # Enforce the controlled vocabulary — discard anything outside it.
        valid = [c for c in candidates if c in ALLOWED_CATEGORIES]
        rejected = set(candidates) - set(valid)
        if rejected:
            # Don't silently drop: surface suggestions for human review.
            # If a rejected value keeps appearing across recipes it may be worth
            # adding to ALLOWED_CATEGORIES and docs/TAXONOMY.md.
            self.logger.warning(
                "LLM suggested categories outside the controlled vocabulary "
                f"(discarded): {rejected}. "
                "If these are reasonable, add them to ALLOWED_CATEGORIES and docs/TAXONOMY.md."
            )
        return valid


# ── Orchestrator ───────────────────────────────────────────────────────────


class RecipeOrganizer:
    """Orchestrates tag and category generation for Mealie recipes.

    Fetches each recipe once, applies both generators in-place, then persists
    with a single update call — minimising API round-trips.
    """

    def __init__(self, settings: Settings | None = None, dry_run: bool = False) -> None:
        """Initialise the organiser, creating Mealie client and translator from settings."""
        self.settings = settings or get_settings()
        self.mealie_client = MealieClient(self.settings)
        self.translator = RecipeTranslator(self.settings)
        self.logger = get_logger(__name__)
        self.dry_run = dry_run
        self._tag_gen = TagGenerator(self.mealie_client, self.translator, dry_run)
        self._cat_gen = CategoryGenerator(self.mealie_client, self.translator, dry_run)

    @staticmethod
    def is_organised(recipe: dict[str, Any]) -> bool:
        """Return True if this recipe has already been organised (tagged and categorised)."""
        extras = recipe.get("extras") or {}
        return str(extras.get(EXTRAS_ORGANISED_KEY, "")).lower() in {"true", "1"}

    @staticmethod
    def _mark_as_organised(recipe: dict[str, Any]) -> None:
        """Stamp extras.organised = 'true' into the recipe dict in-place."""
        if "extras" not in recipe:
            recipe["extras"] = {}
        recipe["extras"][EXTRAS_ORGANISED_KEY] = "true"

    def process_recipe(
        self,
        recipe_slug: str,
        generate_tags: bool = True,
        generate_categories: bool = True,
        skip_organised: bool = False,
    ) -> bool:
        """Generate and persist tags/categories for a single recipe.

        Args:
            recipe_slug: The recipe slug/id to process.
            generate_tags: Whether to run the tag generator.
            generate_categories: Whether to run the category generator.
            skip_organised: When True, return immediately if the recipe is already
                marked as organised (extras.organised = 'true'). The CLI sets this
                to False so ad-hoc runs always re-process.

        Returns:
            True if processing was successful (or skipped as already done).
        """
        recipe = self.mealie_client.get_recipe_details(recipe_slug)
        if not recipe:
            self.logger.error(f"Recipe not found: {recipe_slug}")
            return False

        recipe_name = recipe.get("name", recipe_slug)

        if skip_organised and self.is_organised(recipe):
            self.logger.debug(f"Skipping already organised recipe: {recipe_name}")
            return True

        self.logger.info(f"Organising recipe: {recipe_name}")

        success = True
        if generate_tags:
            success = self._tag_gen.apply_to_recipe(recipe) and success
        if generate_categories:
            success = self._cat_gen.apply_to_recipe(recipe) and success

        if self.dry_run:
            return success

        # Stamp the organised flag in the same payload — no extra API call needed.
        self._mark_as_organised(recipe)

        if not self.mealie_client.update_recipe(recipe_slug, recipe):
            self.logger.error(f"Failed to update recipe '{recipe_name}'")
            return False

        return success

    def process_all_recipes(
        self,
        generate_tags: bool = True,
        generate_categories: bool = True,
        skip_organised: bool = True,
    ) -> dict[str, int]:
        """Generate and persist tags/categories for every recipe on the server.

        Args:
            generate_tags: Whether to run the tag generator.
            generate_categories: Whether to run the category generator.
            skip_organised: When True (default), recipes that already carry
                extras.organised = 'true' are skipped and counted under 'skipped'.
                Pass False (e.g. from the CLI) to force re-processing of all recipes.

        Returns:
            Stats dict with keys: total, updated, skipped, failed.
        """
        import time

        stats: dict[str, int] = {"total": 0, "updated": 0, "skipped": 0, "failed": 0}

        all_recipes = self.mealie_client.get_all_recipes()
        stats["total"] = len(all_recipes)

        if not all_recipes:
            self.logger.warning("No recipes found on the server.")
            return stats

        self.logger.info(f"Organising {stats['total']} recipes...")

        for i, recipe in enumerate(all_recipes, 1):
            recipe_slug = recipe.get("slug") or recipe.get("id")
            if not recipe_slug:
                self.logger.warning("Recipe missing slug/id, skipping")
                stats["skipped"] += 1
                continue

            self.logger.info(
                f"[{i}/{stats['total']}] {recipe.get('name', recipe_slug)}"
            )

            try:
                success = self.process_recipe(
                    recipe_slug,
                    generate_tags=generate_tags,
                    generate_categories=generate_categories,
                    skip_organised=skip_organised,
                )
                if success:
                    stats["updated"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                self.logger.error(f"Error organising '{recipe_slug}': {e}")
                stats["failed"] += 1

            # Polite delay between recipes to avoid hammering LLM/Mealie APIs
            if i < stats["total"]:
                time.sleep(1)

        return stats

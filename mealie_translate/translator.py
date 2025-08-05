"""OpenAI translation service for recipe content."""

import time
from typing import Any

from openai import OpenAI

from .config import Settings


class RecipeTranslator:
    """Handles translation of recipe content using OpenAI ChatGPT."""

    # Reusable prompt components
    UNIT_CONVERSION_RULES = """
UNIT CONVERSION RULES:
Convert ALL imperial units to metric equivalents and ROUND to the nearest multiple of 5:

VOLUME CONVERSIONS:
- cups to ml (1 cup = 240 ml, round to nearest 5 ml)
- liquid ounces (fl oz) to ml (1 fl oz = 30 ml, round to nearest 5 ml)
- gallons to ml (1 gallon = 3785 ml, round to nearest 5 ml)
- tablespoons (tbsp) to ml (1 tbsp = 15 ml, already multiple of 5)
- teaspoons (tsp) to ml (1 tsp = 5 ml, already multiple of 5)
- pints to ml (1 pint = 473 ml, round to 475 ml)
- quarts to ml (1 quart = 946 ml, round to 945 ml)

MASS CONVERSIONS:
- pounds (lbs) to g (1 lb = 454 g, round to 455 g)
- ounces (oz) to g (1 oz = 28 g, round to 30 g)
- stone to g (1 stone = 6350 g, already multiple of 5)

TEMPERATURE CONVERSIONS:
- F or Fahrenheit to C (C = (F - 32) x 5/9, round to nearest 5C)

ROUNDING EXAMPLES:
- 227g becomes 225g, 454g becomes 455g, 163C becomes 165C, 175C stays 175C
- Always round to make measurements practical for home cooking
"""

    TRANSLATION_RULES_BASE = """
TRANSLATION RULES:
1. Only translate text content, preserve all formatting, HTML tags, and special characters
2. Keep the meaning and tone intact
3. If the text is already in {target_language}, keep the translation unchanged
4. Do not add explanations, comments, or additional text
5. Return ONLY the translated and converted text
"""

    SYSTEM_MESSAGE = """You are a professional recipe translator and unit converter specializing in accurate, context-aware translations and imperial to metric conversions.
You must preserve the exact structure and format of the input while translating text content AND converting imperial units to metric equivalents.
Never add explanations, commentary, or modify the format of the response."""

    def __init__(self, settings: Settings):
        """Initialize the translator.

        Args:
            settings: Application settings containing API configuration
        """
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.target_language = settings.target_language
        self.max_retries = settings.max_retries
        self.retry_delay = settings.retry_delay
        self.model = settings.openai_model

    def translate_recipe(self, recipe: dict[str, Any]) -> dict[str, Any]:
        """Translate a complete recipe to the target language.

        Args:
            recipe: Recipe dictionary with content to translate

        Returns:
            Updated recipe dictionary with translated content

        Raises:
            Exception: If translation fails after all retries
        """
        translated_recipe = recipe.copy()

        # Translate main fields
        if recipe.get("name"):
            translated_recipe["name"] = self._translate_text(recipe["name"])

        if recipe.get("description"):
            translated_recipe["description"] = self._translate_text(
                recipe["description"]
            )

        # Translate instructions
        if recipe.get("recipeInstructions"):
            translated_recipe["recipeInstructions"] = self._translate_instructions(
                recipe["recipeInstructions"]
            )

        # Translate ingredients
        if recipe.get("recipeIngredient"):
            translated_recipe["recipeIngredient"] = self._translate_ingredients(
                recipe["recipeIngredient"]
            )

        # Translate notes if present
        if recipe.get("notes"):
            translated_recipe["notes"] = self._translate_notes(recipe["notes"])

        return translated_recipe

    def _translate_text(self, text: str) -> str:
        """Translate a single text string.

        Args:
            text: Text to translate

        Returns:
            Translated text
        """
        if not text or not text.strip():
            return text

        translation_rules = self.TRANSLATION_RULES_BASE.format(
            target_language=self.target_language
        )

        conversion_examples = """
Examples:
- "2 cups flour" becomes "480 ml flour"
- "1 pound butter" becomes "455 g butter"
- "350F" becomes "175C"
- "1 tablespoon oil" becomes "15 ml oil"
- "8 ounces cream cheese" becomes "225 g cream cheese"
- "325F" becomes "165C"
"""

        prompt = f"""
You are a professional recipe translator and unit converter. Translate the following text to {self.target_language} AND convert imperial units to metric.

{translation_rules}

{self.UNIT_CONVERSION_RULES}

{conversion_examples}

Text to translate and convert: {text}
"""

        return self._call_openai(prompt)

    def _translate_instructions(
        self, instructions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Translate recipe instructions.

        Args:
            instructions: List of instruction dictionaries

        Returns:
            List of translated instruction dictionaries
        """
        if not instructions:
            return instructions

        translated_instructions = []

        for instruction in instructions:
            translated_instruction = instruction.copy()

            if instruction.get("text"):
                translated_instruction["text"] = self._translate_text(
                    instruction["text"]
                )

            translated_instructions.append(translated_instruction)

        return translated_instructions

    def _translate_ingredients(
        self, ingredients: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Translate recipe ingredients.

        Args:
            ingredients: List of ingredient dictionaries

        Returns:
            List of translated ingredient dictionaries
        """
        if not ingredients:
            return ingredients

        # Collect all ingredient texts for batch translation
        ingredient_texts = []
        for ingredient in ingredients:
            if ingredient.get("note"):
                ingredient_texts.append(ingredient["note"])
            if ingredient.get("originalText"):
                ingredient_texts.append(ingredient["originalText"])

        if not ingredient_texts:
            return ingredients

        # Batch translate for efficiency
        translated_texts = self._translate_ingredient_batch(ingredient_texts)

        # Apply translations back to ingredients
        translated_ingredients = []
        text_index = 0

        for ingredient in ingredients:
            translated_ingredient = ingredient.copy()

            if ingredient.get("note"):
                translated_ingredient["note"] = translated_texts[text_index]
                text_index += 1

            if ingredient.get("originalText"):
                translated_ingredient["originalText"] = translated_texts[text_index]
                text_index += 1

            translated_ingredients.append(translated_ingredient)

        return translated_ingredients

    def _translate_ingredient_batch(self, texts: list[str]) -> list[str]:
        """Translate a batch of ingredient texts.

        Args:
            texts: List of texts to translate

        Returns:
            List of translated texts
        """
        if not texts:
            return texts

        # Create numbered list for batch translation
        numbered_texts = "\n".join(f"{i + 1}. {text}" for i, text in enumerate(texts))

        ingredient_translation_rules = f"""
TRANSLATION RULES:
1. ONLY translate ingredient names and descriptions
2. Preserve any formatting, punctuation, and special characters
3. If an ingredient is already in {self.target_language}, keep the translation unchanged
4. Return translations in the EXACT same numbered format, one per line
5. Do not add explanations or additional text
"""

        ingredient_examples = """
Examples:
- "1. 2 cups all-purpose flour" becomes "1. 480 ml all-purpose flour"
- "2. 1 pound ground beef" becomes "2. 455 g ground beef"
- "3. 1 tablespoon olive oil" becomes "3. 15 ml olive oil"
- "4. 8 ounces cream cheese" becomes "4. 225 g cream cheese"
"""

        prompt = f"""
You are a professional recipe translator and unit converter. Translate the following ingredient texts to {self.target_language} AND convert imperial units to metric.

{ingredient_translation_rules}

{self.UNIT_CONVERSION_RULES}

{ingredient_examples}

Ingredients to translate and convert:
{numbered_texts}

Return the translations with unit conversions in the same numbered format:
"""

        response = self._call_openai(prompt)

        # Parse the numbered response back to list
        translated_lines = response.strip().split("\n")
        translated_texts = []

        for line in translated_lines:
            # Remove numbering (e.g., "1. " from start)
            if ". " in line:
                translated_text = line.split(". ", 1)[1]
                translated_texts.append(translated_text)
            else:
                translated_texts.append(line)

        # Ensure we have the same number of translations as inputs
        while len(translated_texts) < len(texts):
            translated_texts.append(texts[len(translated_texts)])

        return translated_texts[: len(texts)]

    def _translate_notes(self, notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Translate recipe notes.

        Args:
            notes: List of note dictionaries

        Returns:
            List of translated note dictionaries
        """
        if not notes:
            return notes

        translated_notes = []

        for note in notes:
            translated_note = note.copy()

            if note.get("title"):
                translated_note["title"] = self._translate_text(note["title"])

            if note.get("text"):
                translated_note["text"] = self._translate_text(note["text"])

            translated_notes.append(translated_note)

        return translated_notes

    def _call_openai(self, prompt: str, model: str | None = None) -> str:
        """Make a call to OpenAI API with retry logic.

        Args:
            prompt: The prompt to send to OpenAI
            model: Optional model override (for testing different models)

        Returns:
            The response text from OpenAI

        Raises:
            Exception: If all retries fail
        """
        model_to_use = model or self.model

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model_to_use,
                    messages=[
                        {
                            "role": "system",
                            "content": self.SYSTEM_MESSAGE,
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=2000,  # Increased for longer recipes
                    temperature=0.1,  # Low temperature for consistent translations
                )

                content = response.choices[0].message.content
                return content.strip() if content else ""

            except Exception as e:
                print(
                    f"OpenAI API error (attempt {attempt + 1}/{self.max_retries}): {e}"
                )

                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2**attempt))  # Exponential backoff
                else:
                    raise Exception(
                        f"Failed to translate after {self.max_retries} attempts: {e}"
                    ) from e

        return ""  # Fallback return

    def translate_text_with_model(self, text: str, model: str | None = None) -> str:
        """Translate text with optional model override for testing.

        This method is designed for use by model comparison tools to test
        different models while using the exact same prompt construction logic.

        Args:
            text: Text to translate
            model: Optional model override (for testing different models)

        Returns:
            Translated text
        """
        if not text or not text.strip():
            return text

        translation_rules = self.TRANSLATION_RULES_BASE.format(
            target_language=self.target_language
        )

        conversion_examples = """
Examples:
- "2 cups flour" becomes "480 ml flour"
- "1 pound butter" becomes "455 g butter"
- "350F" becomes "175C"
- "1 tablespoon oil" becomes "15 ml oil"
- "8 ounces cream cheese" becomes "225 g cream cheese"
- "325F" becomes "165C"
"""

        prompt = f"""
You are a professional recipe translator and unit converter. Translate the following text to {self.target_language} AND convert imperial units to metric.

{translation_rules}

{self.UNIT_CONVERSION_RULES}

{conversion_examples}

Text to translate and convert: {text}
"""

        return self._call_openai(prompt, model)

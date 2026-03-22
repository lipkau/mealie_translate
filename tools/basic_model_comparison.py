#!/usr/bin/env python3
"""Model comparison script to test different GPT models across the full feature set.

Covers three dimensions of the production feature set:
  1. Unit conversion  — edge cases (fractions, stick of butter, Gas Mark, passthrough)
  2. Tagging          — taxonomy rule compliance (no category-word bleed, expected tags present)
  3. Categorisation   — controlled-vocabulary compliance (ALLOWED_CATEGORIES only)

This script directly calls methods from the production RecipeTranslator and
re-uses the organizer prompt constants, ensuring results stay in sync when
prompts change.
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Any

project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from mealie_translate.config import get_settings
from mealie_translate.organizer import (
    ALLOWED_CATEGORIES,
    CATEGORY_GENERATION_PROMPT,
    TAG_GENERATION_PROMPT,
)
from mealie_translate.translator import RecipeTranslator


class ModelComparison:
    """Compare different GPT models across the full production feature set."""

    def __init__(self):
        self.settings = get_settings()
        if not self.settings.openai_api_key:
            raise ValueError("OpenAI API key is required for model comparison")

        self.models = [
            "gpt-5.4-nano",
            "gpt-5.4-mini",
            "gpt-5.4",
            "gpt-4.1-nano",
            "gpt-4.1-mini",
            "gpt-4.1",
            "gpt-4o-mini",
            "gpt-4o",
        ]

        self.unit_cases = [
            {
                "name": "Fraction: 3/4 cup",
                "input": "3/4 cup all-purpose flour",
                "expected_elements": ["180", "ml"],
            },
            {
                "name": "Fraction: 1/3 cup",
                "input": "1/3 cup honey",
                "expected_elements": ["80", "ml"],
            },
            {
                "name": "Stick of butter (domain knowledge)",
                "input": "2 sticks of butter, softened",
                "expected_elements": ["226", "g"],
            },
            {
                "name": "Mixed number: 2 1/4 cups",
                "input": "2 1/4 cups whole milk",
                "expected_elements": ["540", "ml"],
            },
            {
                "name": "Gas Mark temperature (UK unit)",
                "input": "Preheat the oven to Gas Mark 6",
                "expected_elements": ["200", "°C"],
            },
            {
                "name": "Passthrough — already metric",
                "input": "Bring 500 ml of water to a boil at 100°C",
                "expected_elements": ["500", "ml", "100", "°C"],
            },
            {
                "name": "Multi-unit instruction",
                "input": "Rub 2 lbs of pork with 1/4 cup spice blend and roast at 325°F for 2 hours",
                "expected_elements": ["910", "g", "60", "ml", "165", "°C"],
            },
        ]

        _category_word_list = sorted(ALLOWED_CATEGORIES)

        self.tag_cases = [
            {
                "name": "Carbonara — cuisine + no category bleed",
                "recipe": {
                    "name": "Spaghetti Carbonara",
                    "description": "Classic Roman pasta dish with guanciale, eggs, pecorino and black pepper.",
                    "ingredients": "spaghetti, guanciale, eggs, pecorino romano, black pepper",
                    "available_tags": "",
                    "existing_categories": "dinner",
                    "existing_tags": "",
                },
                "expected_tags": ["italian", "pasta"],
                "forbidden": _category_word_list,
            },
            {
                "name": "Pancakes — no 'breakfast' as a tag",
                "recipe": {
                    "name": "Fluffy Buttermilk Pancakes",
                    "description": "Light and fluffy pancakes with buttermilk and maple syrup.",
                    "ingredients": "flour, buttermilk, eggs, butter, sugar, baking powder, vanilla",
                    "available_tags": "",
                    "existing_categories": "breakfast",
                    "existing_tags": "",
                },
                "expected_tags": ["sweet"],
                "forbidden": ["breakfast", "brunch", "lunch", "dinner"],
            },
        ]

        self.category_cases = [
            {
                "name": "Chocolate Lava Cake → dessert",
                "recipe": {
                    "name": "Chocolate Lava Cake",
                    "description": "Warm chocolate cakes with a molten center, served with ice cream.",
                    "ingredients": "dark chocolate, butter, eggs, sugar, flour, vanilla",
                    "existing_tags": "chocolate, baked, sweet",
                    "existing_categories": "",
                },
                "expected_categories": ["dessert"],
                "must_not_include": ["dinner", "lunch", "breakfast", "main"],
            },
            {
                "name": "Hummus → condiment (no legacy 'main')",
                "recipe": {
                    "name": "Classic Hummus",
                    "description": "Creamy Middle Eastern chickpea dip with tahini, lemon and garlic.",
                    "ingredients": "chickpeas, tahini, lemon juice, garlic, olive oil, cumin",
                    "existing_tags": "middle-eastern, vegetarian, no-cook",
                    "existing_categories": "",
                },
                "expected_categories": ["condiment"],
                "must_not_include": ["main", "dinner"],
            },
        ]

    async def test_model(self, model_name: str) -> dict[str, Any]:
        """Test a specific model across unit conversion, tagging, and categorisation."""
        print(f"\n🧪 Testing model: {model_name}")
        print("-" * 50)

        translator = RecipeTranslator(self.settings)
        total_cases = (
            len(self.unit_cases) + len(self.tag_cases) + len(self.category_cases)
        )

        results: dict[str, Any] = {
            "model": model_name,
            "total_tests": total_cases,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "test_results": [],
            "average_time": 0,
            "total_time": 0,
        }
        total_time = 0.0

        print("  📐 Unit Conversion:")
        for i, tc in enumerate(self.unit_cases, 1):
            print(f"    {i}. {tc['name']}: ", end="")
            start = time.time()
            try:
                output = await translator.translate_text_with_model(
                    tc["input"], model_name
                )
                elapsed = time.time() - start
                total_time += elapsed
                missing = [
                    e
                    for e in tc["expected_elements"]
                    if e.lower() not in output.lower()
                ]
                passed = len(missing) == 0
                if passed:
                    print(f"✅ ({elapsed:.2f}s)")
                    results["passed"] += 1
                else:
                    print(f"❌ Missing: {missing} ({elapsed:.2f}s)")
                    results["failed"] += 1
                results["test_results"].append(
                    {
                        "name": tc["name"],
                        "type": "unit",
                        "input": tc["input"],
                        "output": output,
                        "passed": passed,
                        "time": elapsed,
                    }
                )
            except Exception as e:
                elapsed = time.time() - start
                total_time += elapsed
                print(f"❌ Error: {str(e)[:50]}... ({elapsed:.2f}s)")
                results["errors"] += 1
                results["test_results"].append(
                    {
                        "name": tc["name"],
                        "type": "unit",
                        "output": f"ERROR: {e}",
                        "passed": False,
                        "time": elapsed,
                    }
                )

        print("  🏷️  Tagging:")
        for i, tc in enumerate(self.tag_cases, 1):
            print(f"    {i}. {tc['name']}: ", end="")
            prompt = TAG_GENERATION_PROMPT.format(**tc["recipe"])
            start = time.time()
            try:
                output = await translator._call_openai(prompt, model_name)
                elapsed = time.time() - start
                total_time += elapsed
                tags_raw = [t.strip().lower() for t in output.split(",") if t.strip()]
                violations = [w for w in tc["forbidden"] if w in tags_raw]
                missing_expected = [
                    t
                    for t in tc["expected_tags"]
                    if not any(t in tag for tag in tags_raw)
                ]
                passed = not violations and not missing_expected
                if passed:
                    print(f"✅ ({elapsed:.2f}s)")
                    results["passed"] += 1
                elif violations:
                    print(f"❌ category bleed: {violations} ({elapsed:.2f}s)")
                    results["failed"] += 1
                else:
                    print(f"❌ missing tags: {missing_expected} ({elapsed:.2f}s)")
                    results["failed"] += 1
                results["test_results"].append(
                    {
                        "name": tc["name"],
                        "type": "tag",
                        "output": output,
                        "passed": passed,
                        "time": elapsed,
                    }
                )
            except Exception as e:
                elapsed = time.time() - start
                total_time += elapsed
                print(f"❌ Error: {str(e)[:50]}... ({elapsed:.2f}s)")
                results["errors"] += 1
                results["test_results"].append(
                    {
                        "name": tc["name"],
                        "type": "tag",
                        "output": f"ERROR: {e}",
                        "passed": False,
                        "time": elapsed,
                    }
                )

        print("  📂 Categorisation:")
        for i, tc in enumerate(self.category_cases, 1):
            print(f"    {i}. {tc['name']}: ", end="")
            prompt = CATEGORY_GENERATION_PROMPT.format(**tc["recipe"])
            start = time.time()
            try:
                output = await translator._call_openai(prompt, model_name)
                elapsed = time.time() - start
                total_time += elapsed
                cats_raw = [c.strip().lower() for c in output.split(",") if c.strip()]
                vocab_violations = [c for c in cats_raw if c not in ALLOWED_CATEGORIES]
                missing_expected = [
                    c for c in tc["expected_categories"] if c not in cats_raw
                ]
                wrong = [c for c in tc["must_not_include"] if c in cats_raw]
                passed = not vocab_violations and not missing_expected and not wrong
                if passed:
                    print(f"✅ ({elapsed:.2f}s)")
                    results["passed"] += 1
                elif vocab_violations:
                    print(f"❌ vocab error: {vocab_violations} ({elapsed:.2f}s)")
                    results["failed"] += 1
                elif wrong:
                    print(f"❌ wrong category: {wrong} ({elapsed:.2f}s)")
                    results["failed"] += 1
                else:
                    print(f"❌ missing: {missing_expected} ({elapsed:.2f}s)")
                    results["failed"] += 1
                results["test_results"].append(
                    {
                        "name": tc["name"],
                        "type": "category",
                        "output": output,
                        "passed": passed,
                        "time": elapsed,
                    }
                )
            except Exception as e:
                elapsed = time.time() - start
                total_time += elapsed
                print(f"❌ Error: {str(e)[:50]}... ({elapsed:.2f}s)")
                results["errors"] += 1
                results["test_results"].append(
                    {
                        "name": tc["name"],
                        "type": "category",
                        "output": f"ERROR: {e}",
                        "passed": False,
                        "time": elapsed,
                    }
                )

        results["total_time"] = total_time
        results["average_time"] = total_time / total_cases
        return results

    async def run_comparison(self) -> dict[str, Any]:
        """Run comparison across all models."""
        print("🔬 GPT Model Comparison — Unit Conversion · Tagging · Categorisation")
        print("=" * 70)

        all_results = {}

        for model in self.models:
            try:
                results = await self.test_model(model)
                all_results[model] = results
            except Exception as e:
                print(f"\n❌ Failed to test model {model}: {e}")
                total_cases = (
                    len(self.unit_cases)
                    + len(self.tag_cases)
                    + len(self.category_cases)
                )
                all_results[model] = {
                    "model": model,
                    "error": str(e),
                    "total_tests": total_cases,
                    "passed": 0,
                    "failed": 0,
                    "errors": total_cases,
                }

        return all_results

    def print_summary(self, all_results: dict[str, Any]):
        """Print a summary comparison of all models."""
        print("\n" + "=" * 70)
        print("📊 COMPARISON SUMMARY")
        print("=" * 70)

        sorted_models = sorted(
            all_results.items(),
            key=lambda x: x[1].get("passed", 0) / max(x[1].get("total_tests", 1), 1),
            reverse=True,
        )

        print(
            f"{'Model':<20} {'Success Rate':<12} {'Avg Time':<10} {'Total Time':<12} {'Status'}"
        )
        print("-" * 70)

        for model_name, results in sorted_models:
            if "error" in results:
                print(f"{model_name:<20} {'N/A':<12} {'N/A':<10} {'N/A':<12} ❌ Error")
            else:
                success_rate = (results["passed"] / results["total_tests"]) * 100
                avg_time = results.get("average_time", 0)
                total_time = results.get("total_time", 0)

                status = (
                    "🥇"
                    if success_rate == 100
                    else (
                        "🥈"
                        if success_rate >= 80
                        else "🥉"
                        if success_rate >= 60
                        else "❌"
                    )
                )

                print(
                    f"{model_name:<20} {success_rate:>8.1f}%    {avg_time:>6.2f}s    {total_time:>8.2f}s    {status}"
                )

        print(
            "\n⚠️  Note: success rate covers unit conversion, tagging taxonomy rules, and category vocabulary compliance."
        )

        print("\n🏆 Best performing model:")
        if sorted_models:
            best_model, best_results = sorted_models[0]
            if "error" not in best_results:
                success_rate = (
                    best_results["passed"] / best_results["total_tests"]
                ) * 100
                print(f"   {best_model} - {success_rate:.1f}% success rate")
            else:
                print("   No models completed successfully")


async def async_main():
    """Async main function to run the model comparison."""
    try:
        comparison = ModelComparison()
        results = await comparison.run_comparison()
        comparison.print_summary(results)

        print(
            "\n💾 To see detailed results for any model, check the test_results in the returned data"
        )

        return True

    except Exception as e:
        print(f"❌ Model comparison failed: {e}")
        return False


def main():
    """Main function to run the model comparison."""
    return asyncio.run(async_main())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

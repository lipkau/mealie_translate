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

from _model_comparison_data import (
    AVAILABLE_MODELS,
    CATEGORY_TEST_CASES,
    TAG_TEST_CASES,
    UNIT_TEST_CASES,
)

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

        self.models = AVAILABLE_MODELS
        self.unit_cases = [
            {
                "name": tc["name"],
                "input": tc["input"],
                "expected_elements": tc["key_elements"],
            }
            for tc in UNIT_TEST_CASES
        ]
        self.tag_cases = TAG_TEST_CASES
        self.category_cases = CATEGORY_TEST_CASES

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

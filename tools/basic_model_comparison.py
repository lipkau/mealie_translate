#!/usr/bin/env python3
"""Model comparison script to test different GPT models for recipe translation and unit conversion.

This script directly calls methods from the production RecipeTranslator class,
ensuring perfect consistency and automatic updates when prompts are improved.
"""

import sys
import time
from pathlib import Path
from typing import Any

# Add the package to the Python path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from mealie_translate.config import get_settings
from mealie_translate.translator import RecipeTranslator


class ModelComparison:
    """Compare different GPT models for recipe translation and unit conversion."""

    def __init__(self):
        self.settings = get_settings()
        if not self.settings.openai_api_key:
            raise ValueError("OpenAI API key is required for model comparison")

        # Models to compare - you can update these when new models become available
        self.models = [
            "gpt-3.5-turbo",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
            "gpt-5",
            "gpt-5-mini",
            "gpt-5-nano",
        ]

        # Test cases for comparison
        self.test_cases = [
            {
                "name": "Volume Conversion",
                "input": "2 cups all-purpose flour",
                "expected_elements": ["480", "ml", "flour"],
            },
            {
                "name": "Mass Conversion",
                "input": "1 pound ground beef",
                "expected_elements": ["455", "g", "beef"],
            },
            {
                "name": "Temperature Conversion",
                "input": "Bake at 350°F for 25 minutes",
                "expected_elements": ["175", "°C", "25"],
            },
            {
                "name": "Mixed Units",
                "input": "Mix 8 ounces cream cheese with 1 tablespoon sugar",
                "expected_elements": ["225", "g", "15", "ml"],
            },
        ]

    def test_model(self, model_name: str) -> dict[str, Any]:
        """Test a specific model with all test cases."""
        print(f"\n🧪 Testing model: {model_name}")
        print("-" * 50)

        # Create a translator instance with the specific model
        translator = RecipeTranslator(self.settings)

        # Temporarily override the model
        original_model = None
        results = {
            "model": model_name,
            "total_tests": len(self.test_cases),
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "test_results": [],
            "average_time": 0,
            "total_time": 0,
        }

        total_time = 0

        for i, test_case in enumerate(self.test_cases, 1):
            print(f"  {i}. {test_case['name']}: ", end="")

            start_time = time.time()
            try:
                # Use the translator's method directly - this is TRUE reuse!
                # Any improvements to the prompt logic will automatically be used here
                output = translator.translate_text_with_model(
                    test_case["input"], model_name
                )

                end_time = time.time()
                test_time = end_time - start_time
                total_time += test_time

                # Check if expected elements are present
                missing_elements = []
                for expected in test_case["expected_elements"]:
                    if expected.lower() not in output.lower():
                        missing_elements.append(expected)

                test_result = {
                    "name": test_case["name"],
                    "input": test_case["input"],
                    "output": output,
                    "expected": test_case["expected_elements"],
                    "missing": missing_elements,
                    "passed": len(missing_elements) == 0,
                    "time": test_time,
                }

                if test_result["passed"]:
                    print(f"✅ ({test_time:.2f}s)")
                    results["passed"] += 1
                else:
                    print(f"❌ Missing: {missing_elements} ({test_time:.2f}s)")
                    results["failed"] += 1

                results["test_results"].append(test_result)

            except Exception as e:
                end_time = time.time()
                test_time = end_time - start_time
                total_time += test_time

                print(f"❌ Error: {str(e)[:50]}... ({test_time:.2f}s)")
                results["errors"] += 1
                results["test_results"].append(
                    {
                        "name": test_case["name"],
                        "input": test_case["input"],
                        "output": f"ERROR: {e}",
                        "expected": test_case["expected_elements"],
                        "missing": test_case["expected_elements"],
                        "passed": False,
                        "time": test_time,
                    }
                )

        results["total_time"] = total_time
        results["average_time"] = total_time / len(self.test_cases)

        return results

    def run_comparison(self) -> dict[str, Any]:
        """Run comparison across all models."""
        print("🔬 GPT Model Comparison for Recipe Translation & Unit Conversion")
        print("=" * 70)

        all_results = {}

        for model in self.models:
            try:
                results = self.test_model(model)
                all_results[model] = results
            except Exception as e:
                print(f"\n❌ Failed to test model {model}: {e}")
                all_results[model] = {
                    "model": model,
                    "error": str(e),
                    "total_tests": len(self.test_cases),
                    "passed": 0,
                    "failed": 0,
                    "errors": len(self.test_cases),
                }

        return all_results

    def print_summary(self, all_results: dict[str, Any]):
        """Print a summary comparison of all models."""
        print("\n" + "=" * 70)
        print("📊 COMPARISON SUMMARY")
        print("=" * 70)

        # Sort models by success rate
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


def main():
    """Main function to run the model comparison."""
    try:
        comparison = ModelComparison()
        results = comparison.run_comparison()
        comparison.print_summary(results)

        # Optionally save detailed results
        print(
            "\n💾 To see detailed results for any model, check the test_results in the returned data"
        )

        return True

    except Exception as e:
        print(f"❌ Model comparison failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

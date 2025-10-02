#!/usr/bin/env python3
"""Detailed model comparison with full output analysis.
Easily configurable for new models like gpt-4.1, gpt-4.1-mini, gpt-4.1-nano when available.

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

# CONFIGURATION: Update this list when new models become available
AVAILABLE_MODELS = [
    "gpt-4o-mini",  # Currently used in production
    "gpt-4o",  # More powerful but slower
    "gpt-3.5-turbo",  # Faster but less accurate
    "gpt-4.1",  # Uncomment when available
    "gpt-4.1-mini",  # Uncomment when available
    "gpt-4.1-nano",  # Uncomment when available
]

# Test cases focusing on unit conversion accuracy
TEST_CASES = [
    {
        "name": "1 Cup Flour Consistency",
        "input": "1 cup flour",
        "expected_output": "240 ml flour",
        "key_elements": ["240", "ml"],
    },
    {
        "name": "1 Cup Sugar Consistency",
        "input": "1 cup sugar",
        "expected_output": "240 ml sugar",
        "key_elements": ["240", "ml"],
    },
    {
        "name": "Simple Volume (2 cups)",
        "input": "2 cups flour",
        "expected_output": "480 ml flour",
        "key_elements": ["480", "ml"],
    },
    {
        "name": "Simple Mass",
        "input": "1 pound butter",
        "expected_output": "455 g butter",
        "key_elements": ["455", "g"],
    },
    {
        "name": "Temperature",
        "input": "Bake at 350°F",
        "expected_output": "Bake at 175°C",
        "key_elements": ["175", "°C"],
    },
    {
        "name": "Small Volumes",
        "input": "1 tablespoon oil and 1 teaspoon salt",
        "expected_output": "15 ml oil and 5 ml salt",
        "key_elements": ["15", "ml", "5", "ml"],
    },
    {
        "name": "Mixed Complex",
        "input": "Mix 1.5 cups sugar with 8 ounces cream cheese at 325°F",
        "expected_output": "Mix 360 ml sugar with 225 g cream cheese at 165°C",
        "key_elements": ["360", "ml", "225", "g", "165", "°C"],
    },
]


def test_single_model(model_name: str, settings) -> dict[str, Any]:
    """Test a single model with detailed output analysis."""
    print(f"\n🔬 Testing {model_name}")
    print("=" * 60)

    translator = RecipeTranslator(settings)
    results = {
        "model": model_name,
        "tests": [],
        "summary": {
            "total": len(TEST_CASES),
            "passed": 0,
            "partial": 0,
            "failed": 0,
            "total_time": 0,
            "avg_time": 0,
        },
    }

    total_time = 0

    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Input: {test_case['input']}")
        print(f"   Expected: {test_case['expected_output']}")

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

            print(f"   Output: {output}")
            print(f"   Time: {test_time:.2f}s")

            # Analyze accuracy
            found_elements = []
            missing_elements = []

            for element in test_case["key_elements"]:
                if element.lower() in output.lower():
                    found_elements.append(element)
                else:
                    missing_elements.append(element)

            # Determine test result
            if len(missing_elements) == 0:
                status = "✅ PASSED"
                results["summary"]["passed"] += 1
            elif len(found_elements) > len(missing_elements):
                status = "🟡 PARTIAL"
                results["summary"]["partial"] += 1
            else:
                status = "❌ FAILED"
                results["summary"]["failed"] += 1

            print(f"   Status: {status}")
            if missing_elements:
                print(f"   Missing: {missing_elements}")

            # Store detailed results
            test_result = {
                "name": test_case["name"],
                "input": test_case["input"],
                "expected": test_case["expected_output"],
                "output": output,
                "key_elements": test_case["key_elements"],
                "found_elements": found_elements,
                "missing_elements": missing_elements,
                "time": test_time,
                "status": status,
            }

            results["tests"].append(test_result)

        except Exception as e:
            end_time = time.time()
            test_time = end_time - start_time
            total_time += test_time

            print(f"   Output: ERROR - {e}")
            print(f"   Time: {test_time:.2f}s")
            print("   Status: ❌ ERROR")

            results["summary"]["failed"] += 1
            results["tests"].append(
                {
                    "name": test_case["name"],
                    "input": test_case["input"],
                    "expected": test_case["expected_output"],
                    "output": f"ERROR: {e}",
                    "error": str(e),
                    "time": test_time,
                    "status": "❌ ERROR",
                }
            )

    results["summary"]["total_time"] = total_time
    results["summary"]["avg_time"] = total_time / len(TEST_CASES)

    return results


def print_comparison_summary(all_results: list[dict[str, Any]]):
    """Print a comprehensive comparison summary."""
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE MODEL COMPARISON SUMMARY")
    print("=" * 80)

    # Sort by success rate, then by speed
    sorted_results = sorted(
        all_results,
        key=lambda x: (
            x["summary"]["passed"] / x["summary"]["total"],
            -x["summary"]["avg_time"],  # Negative for faster = better
        ),
        reverse=True,
    )

    print(
        f"{'Model':<15} {'Passed':<7} {'Partial':<8} {'Failed':<7} {'Success%':<9} {'Avg Time':<10} {'Total Time'}"
    )
    print("-" * 80)

    for result in sorted_results:
        summary = result["summary"]
        success_rate = (summary["passed"] / summary["total"]) * 100

        print(
            f"{result['model']:<15} "
            f"{summary['passed']:<7} "
            f"{summary['partial']:<8} "
            f"{summary['failed']:<7} "
            f"{success_rate:>6.1f}%   "
            f"{summary['avg_time']:>6.2f}s    "
            f"{summary['total_time']:>6.2f}s"
        )

    # Best model analysis
    if sorted_results:
        best = sorted_results[0]
        print(f"\n🏆 Best Overall: {best['model']}")
        print(
            f"   Success Rate: {(best['summary']['passed'] / best['summary']['total'] * 100):.1f}%"
        )
        print(f"   Average Time: {best['summary']['avg_time']:.2f}s")

        # Show what makes it best
        print("\n🔍 Detailed Analysis:")
        for test in best["tests"]:
            status_icon = (
                "✅"
                if test["status"] == "✅ PASSED"
                else "🟡"
                if "PARTIAL" in test["status"]
                else "❌"
            )
            print(f"   {status_icon} {test['name']}: {test['output']}")


def main():
    """Run the detailed model comparison."""
    print("🔬 DETAILED GPT MODEL COMPARISON")
    print("Recipe Translation & Imperial-to-Metric Unit Conversion")
    print("=" * 80)

    try:
        settings = get_settings()
        if not settings.openai_api_key:
            print("❌ OpenAI API key is required")
            return False

        all_results = []

        for model in AVAILABLE_MODELS:
            try:
                result = test_single_model(model, settings)
                all_results.append(result)
            except Exception as e:
                print(f"❌ Failed to test {model}: {e}")

        if all_results:
            print_comparison_summary(all_results)

        print("\n💡 To test GPT-4.1 models when available:")
        print("   1. Uncomment the model names in AVAILABLE_MODELS")
        print("   2. Run this script again")

        return True

    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

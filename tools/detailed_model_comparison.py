#!/usr/bin/env python3
"""Detailed model comparison with full output analysis.

Tests three dimensions of the production feature set:
  1. Unit conversion  — edge cases (fractions, stick of butter, Gas Mark, passthrough)
  2. Tagging          — taxonomy rule compliance (no category-word bleed, expected tags present)
  3. Categorisation   — controlled-vocabulary compliance (ALLOWED_CATEGORIES only)

This script calls production methods from RecipeTranslator and re-uses the
organizer prompt constants directly, so results stay in sync when prompts change.
"""

import sys
import time
from pathlib import Path
from typing import Any

# Add the package to the Python path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from mealie_translate.config import get_settings
from mealie_translate.organizer import (
    ALLOWED_CATEGORIES,
    CATEGORY_GENERATION_PROMPT,
    TAG_GENERATION_PROMPT,
)
from mealie_translate.translator import RecipeTranslator

# CONFIGURATION: Update this list when new models become available
# Prices per 1M tokens (input / output) as of March 2026
AVAILABLE_MODELS = [
    # gpt-5.4 flagship series
    "gpt-5.4-nano",  # $0.20 / $1.25
    "gpt-5.4-mini",  # $0.75 / $4.50
    "gpt-5.4",  # $2.50 / $15.00
    # gpt-4.1 series
    "gpt-4.1-nano",  # cheapest in series
    "gpt-4.1-mini",  # mid-tier
    "gpt-4.1",  # main model
    # gpt-4o series (legacy reference)
    "gpt-4o-mini",  # production default
    "gpt-4o",  # previous flagship
]

# ── Unit conversion tests (harder edge cases) ────────────────────────────────
# These go beyond trivial whole-number values to expose real capability gaps.
UNIT_TEST_CASES = [
    {
        "name": "Fraction: 3/4 cup",
        "input": "3/4 cup all-purpose flour",
        "expected_output": "180 ml all-purpose flour",
        "key_elements": ["180", "ml"],
    },
    {
        "name": "Fraction: 1/3 cup",
        "input": "1/3 cup honey",
        "expected_output": "80 ml honey",
        "key_elements": ["80", "ml"],
    },
    {
        "name": "Stick of butter (domain knowledge)",
        "input": "2 sticks of butter, softened",
        "expected_output": "226 g butter, softened",
        "key_elements": ["226", "g"],
    },
    {
        "name": "Mixed number: 2 1/4 cups",
        "input": "2 1/4 cups whole milk",
        "expected_output": "540 ml whole milk",
        "key_elements": ["540", "ml"],
    },
    {
        "name": "Gas Mark temperature (UK unit)",
        "input": "Preheat the oven to Gas Mark 6",
        "expected_output": "Preheat the oven to 200°C",
        "key_elements": ["200", "°C"],
    },
    {
        "name": "Passthrough — already metric",
        "input": "Bring 500 ml of water to a boil at 100°C",
        "expected_output": "Bring 500 ml of water to a boil at 100°C",
        "key_elements": ["500", "ml", "100", "°C"],
    },
    {
        "name": "Multi-unit instruction",
        "input": "Rub 2 lbs of pork with 1/4 cup spice blend and roast at 325°F for 2 hours",
        "expected_output": "Rub 910 g pork with 60 ml spice blend and roast at 165°C for 2 hours",
        "key_elements": ["910", "g", "60", "ml", "165", "°C"],
    },
]

# ── Tagging tests ─────────────────────────────────────────────────────────────
# Verifies two rules from TAG_GENERATION_PROMPT:
#   • expected_tags must appear (relevance)
#   • forbidden words must NOT appear (category bleed — taxonomy rule #1)
_CATEGORY_WORD_LIST = sorted(ALLOWED_CATEGORIES)

TAG_TEST_CASES = [
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
        "forbidden": _CATEGORY_WORD_LIST,  # Taxonomy rule: category words must not appear as tags
    },
    {
        "name": "Pancakes — no 'breakfast' as a tag",
        "recipe": {
            "name": "Fluffy Buttermilk Pancakes",
            "description": "Light and fluffy pancakes made with buttermilk and vanilla, served with maple syrup.",
            "ingredients": "flour, buttermilk, eggs, butter, sugar, baking powder, vanilla extract",
            "available_tags": "",
            "existing_categories": "breakfast",
            "existing_tags": "",
        },
        "expected_tags": ["sweet"],
        # Breakfast foods commonly bleed category words into tags — this catches it
        "forbidden": ["breakfast", "brunch", "lunch", "dinner"],
    },
]

# ── Category tests ─────────────────────────────────────────────────────────────
# Verifies two rules from CATEGORY_GENERATION_PROMPT:
#   • all returned values must be in ALLOWED_CATEGORIES (vocabulary compliance)
#   • expected_categories must appear (correct assignment)
#   • must_not_include words must not appear (wrong assignment)
CATEGORY_TEST_CASES = [
    {
        "name": "Chocolate Lava Cake → dessert",
        "recipe": {
            "name": "Chocolate Lava Cake",
            "description": "Warm individual chocolate cakes with a molten center, served with vanilla ice cream.",
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
            "ingredients": "chickpeas, tahini, lemon juice, garlic cloves, olive oil, cumin, paprika",
            "existing_tags": "middle-eastern, vegetarian, no-cook",
            "existing_categories": "",
        },
        "expected_categories": ["condiment"],
        "must_not_include": [
            "main",
            "dinner",
        ],  # 'main' is explicitly banned per the prompt
    },
]


def _run_unit_tests(
    translator: RecipeTranslator, model_name: str
) -> list[dict[str, Any]]:
    """Run unit conversion tests and return per-test results."""
    results = []
    for i, tc in enumerate(UNIT_TEST_CASES, 1):
        print(f"\n  [{i}/{len(UNIT_TEST_CASES)}] {tc['name']}")
        print(f"   Input:    {tc['input']}")
        print(f"   Expected: {tc['expected_output']}")
        start = time.time()
        try:
            output = translator.translate_text_with_model(tc["input"], model_name)
            elapsed = time.time() - start
            found = [e for e in tc["key_elements"] if e.lower() in output.lower()]
            missing = [e for e in tc["key_elements"] if e.lower() not in output.lower()]
            if not missing:
                status = "✅ PASSED"
            elif len(found) > len(missing):
                status = "🟡 PARTIAL"
            else:
                status = "❌ FAILED"
            print(f"   Output:   {output}")
            print(f"   Status:   {status}  ({elapsed:.2f}s)")
            if missing:
                print(f"   Missing:  {missing}")
            results.append(
                {
                    "name": tc["name"],
                    "input": tc["input"],
                    "expected": tc["expected_output"],
                    "output": output,
                    "found": found,
                    "missing": missing,
                    "status": status,
                    "time": elapsed,
                }
            )
        except Exception as e:
            elapsed = time.time() - start
            print(f"   Output:   ERROR — {e}")
            print(f"   Status:   ❌ ERROR  ({elapsed:.2f}s)")
            results.append(
                {
                    "name": tc["name"],
                    "input": tc["input"],
                    "expected": tc["expected_output"],
                    "output": f"ERROR: {e}",
                    "found": [],
                    "missing": tc["key_elements"],
                    "status": "❌ ERROR",
                    "time": elapsed,
                }
            )
    return results


def _run_tag_tests(
    translator: RecipeTranslator, model_name: str
) -> list[dict[str, Any]]:
    """Run tagging tests and return per-test results."""
    results = []
    for i, tc in enumerate(TAG_TEST_CASES, 1):
        print(f"\n  [{i}/{len(TAG_TEST_CASES)}] {tc['name']}")
        prompt = TAG_GENERATION_PROMPT.format(**tc["recipe"])
        start = time.time()
        try:
            output = translator._call_openai(prompt, model_name)
            elapsed = time.time() - start
            tags_raw = [t.strip().lower() for t in output.split(",") if t.strip()]
            missing_expected = [
                t for t in tc["expected_tags"] if not any(t in tag for tag in tags_raw)
            ]
            violations = [w for w in tc["forbidden"] if w in tags_raw]
            if not missing_expected and not violations:
                status = "✅ PASSED"
            elif not violations:
                status = "🟡 PARTIAL"  # has some expected tags but none forbidden
            else:
                status = "❌ FAILED"  # category word used as tag: taxonomy violation
            print(f"   Output:      {output}")
            print(f"   Status:      {status}  ({elapsed:.2f}s)")
            if missing_expected:
                print(f"   Missing tags:   {missing_expected}")
            if violations:
                print(
                    f"   CAT violations: {violations}  ← category words used as tags!"
                )
            results.append(
                {
                    "name": tc["name"],
                    "output": output,
                    "tags": tags_raw,
                    "missing_expected": missing_expected,
                    "violations": violations,
                    "status": status,
                    "time": elapsed,
                }
            )
        except Exception as e:
            elapsed = time.time() - start
            print(f"   Output:   ERROR — {e}")
            print(f"   Status:   ❌ ERROR  ({elapsed:.2f}s)")
            results.append(
                {
                    "name": tc["name"],
                    "output": f"ERROR: {e}",
                    "tags": [],
                    "missing_expected": tc["expected_tags"],
                    "violations": [],
                    "status": "❌ ERROR",
                    "time": elapsed,
                }
            )
    return results


def _run_category_tests(
    translator: RecipeTranslator, model_name: str
) -> list[dict[str, Any]]:
    """Run categorisation tests and return per-test results."""
    results = []
    for i, tc in enumerate(CATEGORY_TEST_CASES, 1):
        print(f"\n  [{i}/{len(CATEGORY_TEST_CASES)}] {tc['name']}")
        prompt = CATEGORY_GENERATION_PROMPT.format(**tc["recipe"])
        start = time.time()
        try:
            output = translator._call_openai(prompt, model_name)
            elapsed = time.time() - start
            cats_raw = [c.strip().lower() for c in output.split(",") if c.strip()]
            vocab_violations = [c for c in cats_raw if c not in ALLOWED_CATEGORIES]
            missing_expected = [
                c for c in tc["expected_categories"] if c not in cats_raw
            ]
            wrong_assigned = [c for c in tc["must_not_include"] if c in cats_raw]
            if not vocab_violations and not missing_expected and not wrong_assigned:
                status = "✅ PASSED"
            elif not vocab_violations and not wrong_assigned:
                status = "🟡 PARTIAL"  # correct vocab but missing a category
            else:
                status = "❌ FAILED"
            print(f"   Output:       {output}")
            print(f"   Status:       {status}  ({elapsed:.2f}s)")
            if missing_expected:
                print(f"   Missing cats: {missing_expected}")
            if vocab_violations:
                print(
                    f"   Vocab errors: {vocab_violations}  ← not in ALLOWED_CATEGORIES!"
                )
            if wrong_assigned:
                print(f"   Wrong cats:   {wrong_assigned}")
            results.append(
                {
                    "name": tc["name"],
                    "output": output,
                    "categories": cats_raw,
                    "missing_expected": missing_expected,
                    "vocab_violations": vocab_violations,
                    "wrong_assigned": wrong_assigned,
                    "status": status,
                    "time": elapsed,
                }
            )
        except Exception as e:
            elapsed = time.time() - start
            print(f"   Output:   ERROR — {e}")
            print(f"   Status:   ❌ ERROR  ({elapsed:.2f}s)")
            results.append(
                {
                    "name": tc["name"],
                    "output": f"ERROR: {e}",
                    "categories": [],
                    "missing_expected": tc["expected_categories"],
                    "vocab_violations": [],
                    "wrong_assigned": [],
                    "status": "❌ ERROR",
                    "time": elapsed,
                }
            )
    return results


def _count_statuses(tests: list[dict]) -> tuple[int, int, int]:
    passed = sum(1 for t in tests if t["status"] == "✅ PASSED")
    partial = sum(1 for t in tests if "PARTIAL" in t["status"])
    return passed, partial, len(tests) - passed - partial


def test_single_model(model_name: str, settings) -> dict[str, Any]:
    """Test a single model across unit conversion, tagging, and categorisation."""
    print(f"\n{'=' * 60}")
    print(f"🔬 Testing {model_name}")
    print(f"{'=' * 60}")

    translator = RecipeTranslator(settings)

    print("\n📐 Unit Conversion Tests")
    unit_results = _run_unit_tests(translator, model_name)

    print("\n🏷️  Tagging Tests")
    tag_results = _run_tag_tests(translator, model_name)

    print("\n📂 Categorisation Tests")
    cat_results = _run_category_tests(translator, model_name)

    all_tests = unit_results + tag_results + cat_results
    total_time = sum(t["time"] for t in all_tests)
    total = len(all_tests)

    u_pass, u_part, u_fail = _count_statuses(unit_results)
    t_pass, t_part, t_fail = _count_statuses(tag_results)
    c_pass, c_part, c_fail = _count_statuses(cat_results)

    return {
        "model": model_name,
        "unit_results": unit_results,
        "tag_results": tag_results,
        "cat_results": cat_results,
        "summary": {
            "total": total,
            "passed": u_pass + t_pass + c_pass,
            "partial": u_part + t_part + c_part,
            "failed": u_fail + t_fail + c_fail,
            "total_time": total_time,
            "avg_time": total_time / total,
            "units": {
                "pass": u_pass,
                "partial": u_part,
                "fail": u_fail,
                "total": len(unit_results),
            },
            "tags": {
                "pass": t_pass,
                "partial": t_part,
                "fail": t_fail,
                "total": len(tag_results),
            },
            "cats": {
                "pass": c_pass,
                "partial": c_part,
                "fail": c_fail,
                "total": len(cat_results),
            },
        },
    }


def print_comparison_summary(all_results: list[dict[str, Any]]):
    """Print a comprehensive comparison summary with per-section breakdown."""
    print("\n" + "=" * 90)
    print("📊 COMPREHENSIVE MODEL COMPARISON SUMMARY")
    print("=" * 90)

    # Sort by overall pass rate, then by speed
    sorted_results = sorted(
        all_results,
        key=lambda x: (
            x["summary"]["passed"] / x["summary"]["total"],
            -x["summary"]["avg_time"],
        ),
        reverse=True,
    )

    n_units = len(UNIT_TEST_CASES)
    n_tags = len(TAG_TEST_CASES)
    n_cats = len(CATEGORY_TEST_CASES)

    print(
        f"\n{'Model':<15} {'✅Pass':<7} {'🟡Part':<7} {'❌Fail':<7} {'Rate':<8} {'AvgTime':<9}"
        f" [Units/{n_units}] [Tags/{n_tags}] [Cats/{n_cats}]"
    )
    print("-" * 90)

    for r in sorted_results:
        s = r["summary"]
        rate = (s["passed"] / s["total"]) * 100
        u, t, c = s["units"], s["tags"], s["cats"]
        print(
            f"{r['model']:<15} "
            f"{s['passed']:<7} {s['partial']:<7} {s['failed']:<7} "
            f"{rate:>5.1f}%   {s['avg_time']:>5.2f}s    "
            f"[{u['pass']}/{u['total']}]       [{t['pass']}/{t['total']}]      [{c['pass']}/{c['total']}]"
        )

    if sorted_results:
        best = sorted_results[0]
        s = best["summary"]
        print(f"\n🏆 Best Overall: {best['model']}")
        print(
            f"   Pass rate: {(s['passed'] / s['total']) * 100:.1f}%  |  Avg: {s['avg_time']:.2f}s"
        )

        print("\n🔍 Detailed — Unit Conversion:")
        for t in best["unit_results"]:
            icon = (
                "✅"
                if t["status"] == "✅ PASSED"
                else "🟡"
                if "PARTIAL" in t["status"]
                else "❌"
            )
            print(f"   {icon} {t['name']}: {t['output'][:70]}")

        print("\n🔍 Detailed — Tagging:")
        for t in best["tag_results"]:
            icon = (
                "✅"
                if t["status"] == "✅ PASSED"
                else "🟡"
                if "PARTIAL" in t["status"]
                else "❌"
            )
            extra = f"  ⚠️  violations: {t['violations']}" if t.get("violations") else ""
            print(f"   {icon} {t['name']}: {t['output'][:60]}{extra}")

        print("\n🔍 Detailed — Categorisation:")
        for t in best["cat_results"]:
            icon = (
                "✅"
                if t["status"] == "✅ PASSED"
                else "🟡"
                if "PARTIAL" in t["status"]
                else "❌"
            )
            extra = (
                f"  ⚠️  vocab errors: {t['vocab_violations']}"
                if t.get("vocab_violations")
                else ""
            )
            print(f"   {icon} {t['name']}: {t['output'][:60]}{extra}")


def main():
    """Run the detailed model comparison."""
    print("🔬 DETAILED GPT MODEL COMPARISON")
    print("Unit Conversion · Tagging · Categorisation")
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

        print(
            "\n💡 To add or remove models, edit the AVAILABLE_MODELS list at the top of this file."
        )

        return True

    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""Detailed model comparison with full output analysis.

Tests three dimensions of the production feature set:
  1. Unit conversion  — edge cases (fractions, stick of butter, Gas Mark, passthrough)
  2. Tagging          — taxonomy rule compliance (no category-word bleed, expected tags present)
  3. Categorisation   — controlled-vocabulary compliance (ALLOWED_CATEGORIES only)

This script calls production methods from RecipeTranslator and re-uses the
organizer prompt constants directly, so results stay in sync when prompts change.
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


async def _run_unit_tests(
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
            output = await translator.translate_text_with_model(tc["input"], model_name)
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


async def _run_tag_tests(
    translator: RecipeTranslator, model_name: str
) -> list[dict[str, Any]]:
    """Run tagging tests and return per-test results."""
    results = []
    for i, tc in enumerate(TAG_TEST_CASES, 1):
        print(f"\n  [{i}/{len(TAG_TEST_CASES)}] {tc['name']}")
        prompt = TAG_GENERATION_PROMPT.format(**tc["recipe"])
        start = time.time()
        try:
            output = await translator._call_openai(prompt, model_name)
            elapsed = time.time() - start
            tags_raw = [t.strip().lower() for t in output.split(",") if t.strip()]
            missing_expected = [
                t for t in tc["expected_tags"] if not any(t in tag for tag in tags_raw)
            ]
            violations = [w for w in tc["forbidden"] if w in tags_raw]
            if not missing_expected and not violations:
                status = "✅ PASSED"
            elif not violations:
                status = "🟡 PARTIAL"
            else:
                status = "❌ FAILED"
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


async def _run_category_tests(
    translator: RecipeTranslator, model_name: str
) -> list[dict[str, Any]]:
    """Run categorisation tests and return per-test results."""
    results = []
    for i, tc in enumerate(CATEGORY_TEST_CASES, 1):
        print(f"\n  [{i}/{len(CATEGORY_TEST_CASES)}] {tc['name']}")
        prompt = CATEGORY_GENERATION_PROMPT.format(**tc["recipe"])
        start = time.time()
        try:
            output = await translator._call_openai(prompt, model_name)
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
                status = "🟡 PARTIAL"
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


async def test_single_model(model_name: str, settings) -> dict[str, Any]:
    """Test a single model across unit conversion, tagging, and categorisation."""
    print(f"\n{'=' * 60}")
    print(f"🔬 Testing {model_name}")
    print(f"{'=' * 60}")

    translator = RecipeTranslator(settings)

    print("\n📐 Unit Conversion Tests")
    unit_results = await _run_unit_tests(translator, model_name)

    print("\n🏷️  Tagging Tests")
    tag_results = await _run_tag_tests(translator, model_name)

    print("\n📂 Categorisation Tests")
    cat_results = await _run_category_tests(translator, model_name)

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


async def async_main():
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
                result = await test_single_model(model, settings)
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


def main():
    """Main function to run the detailed model comparison."""
    return asyncio.run(async_main())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

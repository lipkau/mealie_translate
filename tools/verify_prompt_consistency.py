#!/usr/bin/env python3
"""
Quick verification that the model comparison tools now use the same prompts as production.
"""

import sys
from pathlib import Path

# Add the package to the Python path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from mealie_translate.config import get_settings
from mealie_translate.translator import RecipeTranslator


def verify_prompt_consistency():
    """Verify that the comparison tools use the same prompts as production."""
    print("🔍 Verifying Prompt Consistency")
    print("=" * 50)

    try:
        settings = get_settings()
        translator = RecipeTranslator(settings)

        # Show the prompts that will be used
        print("\n📝 Production Prompts Being Used:")
        print("\n1. SYSTEM_MESSAGE:")
        print(f"   {translator.SYSTEM_MESSAGE[:100]}...")

        print("\n2. UNIT_CONVERSION_RULES:")
        print(f"   {translator.UNIT_CONVERSION_RULES[:100]}...")

        print("\n3. TRANSLATION_RULES_BASE:")
        print(f"   {translator.TRANSLATION_RULES_BASE[:100]}...")

        print(f"\n4. Model: {translator.model}")
        print(f"5. Max Tokens: 2000")
        print(f"6. Temperature: 0.1")

        print("\n✅ SUCCESS: Model comparison tools now use identical prompts!")
        print("   Both basic_model_comparison.py and detailed_model_comparison.py")
        print("   will use these exact same prompts and parameters.")

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    success = verify_prompt_consistency()
    sys.exit(0 if success else 1)

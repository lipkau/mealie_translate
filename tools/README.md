# Development Tools

This directory contains development and testing tools for the Mealie Recipe Translator project.

📚 **[Complete Development Tools Documentation](../docs/DEVELOPMENT.md#development-tools)**

## Quick Reference

| Tool                           | Purpose                            | Command                                     |
| ------------------------------ | ---------------------------------- | ------------------------------------------- |
| `detailed_model_comparison.py` | Comprehensive GPT model comparison | `python tools/detailed_model_comparison.py` |
| `basic_model_comparison.py`    | Quick model performance testing    | `python tools/basic_model_comparison.py`    |
| `verify_prompt_consistency.py` | Verify prompt consistency          | `python tools/verify_prompt_consistency.py` |
| `generate_tags.py`             | Generate LLM tags for all recipes  | `python tools/generate_tags.py`             |

## Setup

```bash
# Quick setup
make setup
make setup-env  # Edit .env with your API keys

# Run tools
make compare-models        # Detailed comparison
make compare-models-basic  # Basic comparison
make verify-prompts        # Verify consistency
make generate-tags         # Tag all recipes
make generate-tags ARGS="--recipe my-slug"  # Tag one recipe
make generate-tags ARGS="--dry-run"         # Preview without changes
```

For detailed documentation, features, and configuration options, see **[Development Tools Documentation](../docs/DEVELOPMENT.md#development-tools)**.

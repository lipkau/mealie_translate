---
name: recipe-taxonomy
description: Domain knowledge for assigning Mealie recipe categories and tags. USE FOR: classifying recipes; generating or reviewing tags; writing LLM prompts that assign taxonomy; migrating legacy category values; deciding which categories/tags to apply to a new or translated recipe. DO NOT USE FOR: general coding tasks; writing tests; documentation style.
---

# Recipe Taxonomy: Categories and Tags

Recipes are indexed across two orthogonal dimensions: `categories` (course / meal position) and `tags` (descriptive attributes).
Always read the authoritative vocabulary from [`docs/TAXONOMY.md`](../../../docs/TAXONOMY.md) — that file is the single source of truth.
The summary below is provided for quick reference.

## Two Dimensions

| Field        | Role                          | Cardinality               |
| ------------ | ----------------------------- | ------------------------- |
| `categories` | Course / meal position        | Controlled list (~12 values) |
| `tags`       | Descriptive attributes        | Open, extendable, multi-value |

## Allowed Categories (controlled vocabulary)

```text
breakfast · brunch · lunch · dinner · snack · dessert
appetizer · side · drink · condiment · bread · baked-goods
```

> **Migration**: the legacy value `main` must be migrated to `dinner`.

## Tag Dimensions

- **Cuisine**: `brazilian`, `italian`, `french`, `japanese`, `mexican`, `portuguese`, …
- **Main ingredient**: `chicken`, `beef`, `pasta`, `cheese`, `egg`, `potato`, …
- **Dietary**: `vegetarian`, `vegan`, `gluten-free`, `dairy-free`, `low-carb`, …
- **Cooking method**: `baked`, `fried`, `grilled`, `one-pot`, `slow-cooked`, `no-cook`, …
- **Flavor**: `sweet`, `savory`, `spicy`, `creamy`, `smoky`, `tangy`, …
- **Effort**: `quick` (≤30 min), `make-ahead`, `meal-prep`, `weeknight`, `weekend-project`
- **Specific dish**: `pao-de-queijo`, `lasagna`, `brigadeiro`, `feijoada`, …

## Application Rules

1. Assign at least one category before tagging.
2. All values are lowercase; multi-word uses hyphens (`gluten-free`, `pao-de-queijo`).
3. Meal-position words (`breakfast`, `dinner`, …) go in **categories only**, never tags.
4. Reuse existing tags/categories before creating new ones.
5. Specific-dish tags supplement dimensional tags — don't replace them.
6. Normally one tag per dimension (one cuisine, one primary method, etc.) unless both genuinely apply.

## LLM Prompt Contract

When generating tags with an LLM:

- Provide the full controlled category vocabulary and tag dimensions as context.
- Emit only values from the approved lists (or from the existing tag catalog in Mealie).
- Never put meal-position words into tags.
- Never emit categories as tags or vice-versa.

See [`tools/generate_tags.py`](../../../tools/generate_tags.py) for the reference implementation.

## Worked Examples

### Pão de queijo

```text
categories: snack, bread, breakfast
tags:       brazilian, pao-de-queijo, cheese, gluten-free, baked, quick
```

### Chicken stir-fry (weeknight dinner)

```text
categories: dinner
tags:       chicken, stir-fried, quick, weeknight
```

### Chocolate brigadeiro

```text
categories: dessert, snack
tags:       brazilian, brigadeiro, chocolate, sweet, quick, no-cook
```

For the full vocabulary, all worked examples, and migration notes see [`docs/TAXONOMY.md`](../../../docs/TAXONOMY.md).

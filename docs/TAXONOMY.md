# Recipe Taxonomy: Categories and Tags

This document defines the two-dimensional indexing system for Mealie recipes.
It exists so that every tool, LLM prompt, and contributor applies the same vocabulary consistently.

## The Two Dimensions

Mealie provides two organiser fields with different roles in this project:

| Field        | Role                                                       | Cardinality                    | Examples                         |
| ------------ | ---------------------------------------------------------- | ------------------------------ | -------------------------------- |
| `categories` | **Course / meal position** — *when* is the dish eaten?     | Small, controlled (~12 values) | `breakfast`, `dinner`, `dessert` |
| `tags`       | **Descriptive attributes** — *what is it, how is it made?* | Open, extendable, multi-value  | `brazilian`, `chicken`, `quick`  |

A recipe can belong to **one or more categories** and carry **any number of tags**.
The combination of the two dimensions enables precise compound discovery:

| Query                       | Category filter | Tag filter               |
| --------------------------- | --------------- | ------------------------ |
| "Brazilian breakfast"       | `breakfast`     | `brazilian`              |
| "Sweet snack"               | `snack`         | `sweet`                  |
| "Main dish with chicken"    | `dinner`        | `chicken`                |
| "Pão de queijo"             | *(any)*         | `pao-de-queijo`          |
| "Vegetarian Italian dinner" | `dinner`        | `italian` + `vegetarian` |

## Categories — Controlled Vocabulary

The following values are the **only allowed categories**.
Do not create new ones without updating this document.

| Category      | Description                                                                   |
| ------------- | ----------------------------------------------------------------------------- |
| `breakfast`   | Morning meals (sweet or savoury)                                              |
| `brunch`      | Late-morning meals combining breakfast and lunch elements                     |
| `lunch`       | Midday meals                                                                  |
| `dinner`      | Main evening dish (replaces the legacy value `main`)                          |
| `snack`       | Small bites eaten between main meals                                          |
| `dessert`     | Sweet dishes served after a meal or as a treat                                |
| `appetizer`   | Starters served before a main course                                          |
| `side`        | Accompaniments served alongside a main dish                                   |
| `drink`       | Beverages, smoothies, juices, and cocktails                                   |
| `condiment`   | Sauces, dips, dressings, and spreads                                          |
| `bread`       | Breads, rolls, and savoury baked goods (non-dessert)                          |
| `baked-goods` | Sweet baked goods that are not clearly a dessert (e.g. muffins for breakfast) |

> **Migration note**: the legacy category value `main` should be migrated to `dinner`.

## Tags — Structured Dimensions

Tags are free-form but should be drawn from the following semantic dimensions.
Reuse existing tags before inventing new ones.

### Cuisine / Origin

Geographic or cultural origin of the dish.

```text
american, argentinian, brazilian, british, chinese, french, german, greek,
indian, italian, japanese, korean, lebanese, mexican, middle-eastern,
moroccan, portuguese, spanish, thai, turkish
```text

### Main Ingredient

The defining protein, starch, or vegetable.

```text
apple, asparagus, avocado, banana, bean, beef, broccoli, carrot, cheese,
chicken, chocolate, cod, egg, fish, lamb, lemon, lentil, mushroom, pasta,
pork, potato, pumpkin, rice, salmon, seafood, shrimp, spinach, tofu, tomato,
tuna, zucchini
```text

### Dietary Attributes

Suitability flags for restrictions or preferences.

```text
dairy-free, gluten-free, halal, keto, kosher, low-carb, low-fat, nut-free,
paleo, plant-based, vegan, vegetarian, whole30
```text

### Cooking Method

Primary technique used to prepare the dish.

```text
air-fryer, baked, barbecue, boiled, braised, fried, grilled, marinated,
no-cook, one-pot, pressure-cooked, raw, roasted, slow-cooked, smoked,
steamed, stir-fried
```text

### Flavor Profile

Dominant taste or texture characteristic.

```text
citrusy, creamy, crispy, crunchy, hearty, light, mild, refreshing, rich,
savory, smoky, spicy, sweet, tangy, umami, zesty
```text

### Effort / Time

Complexity and time commitment.

```text
5-ingredients, make-ahead, meal-prep, quick, weeknight, weekend-project
```text

> `quick` means ready in 30 minutes or less end-to-end.

### Specific Dish

Use the canonical romanised name for well-known dishes that deserve their own indexed entry.
These coexist with the dimensional tags above.

```text
bolognese, brigadeiro, carbonara, chili, coq-au-vin, feijoada, goulash,
guacamole, hummus, lasagna, moqueca, pao-de-queijo, paella, pesto, ratatouille,
risotto, shakshuka, stroganoff, tiramisu
```text

## Worked Examples

### Pão de queijo

```text
categories: snack, bread, breakfast
tags:       brazilian, pao-de-queijo, cheese, gluten-free, baked, quick
```text

### Brazilian breakfast spread

```text
categories: breakfast
tags:       brazilian, cheese, bread, savory
```text

### Sweet snack

```text
categories: snack
tags:       sweet, quick
```text

### Chicken stir-fry (weeknight dinner)

```text
categories: dinner
tags:       chicken, stir-fried, quick, weeknight, asian-inspired
```text

### Chocolate brigadeiro

```text
categories: dessert, snack
tags:       brazilian, brigadeiro, chocolate, sweet, quick, no-cook
```text

## Application Rules

1. **Categories first**: assign at least one category before tagging.
2. **One tag per dimension**: normally one cuisine, one primary method, one time tag, etc.
   Multiple tags within a dimension are acceptable when genuinely both apply (e.g. `fried` + `baked`).
3. **Reuse before create**: always check existing tags; only introduce a new tag when no existing one fits.
4. **Lowercase and hyphenated**: all category and tag values are lowercase.
   Multi-word values use hyphens, never spaces or underscores (e.g. `gluten-free`, `pao-de-queijo`).
5. **Specific-dish tags supplement, not replace**: a recipe tagged `pao-de-queijo` should also carry
   `brazilian`, `cheese`, `gluten-free`, `baked` — the specific-dish tag helps people search by name,
   the dimensional tags help people discover it through browsing.
6. **No meal-position in tags**: `breakfast`, `dinner`, etc. belong in `categories`, not tags.

## LLM Prompt Contract

Whenever an LLM (OpenAI, Ollama, etc.) is asked to generate tags for a recipe it **must**:

- Receive the full controlled category vocabulary and tag dimensions above as context.
- Emit only values from the approved tag lists (or from the existing tag catalog in Mealie).
- Follow the application rules (reuse before create, lowercase, hyphenated).
- Never put meal-position words into tags.
- Never emit categories as tags or vice-versa.

See [`tools/generate_tags.py`](../tools/generate_tags.py) for the implementation.

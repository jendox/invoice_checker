from app.models.category import Category


def category_style_map(categories: list[Category]) -> dict[str, Category]:
    return {category.slug: category for category in categories}

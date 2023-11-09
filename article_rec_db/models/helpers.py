from enum import StrEnum


class ArticleExcludeReason(StrEnum):
    NOT_ARTICLE = "not_article"
    NOT_IN_HOUSE_ARTICLE = "not_in_house_article"
    TEST_ARTICLE = "test_article"
    HAS_EXCLUDED_TAG = "has_excluded_tag"


class StrategyType(StrEnum):
    POPULARITY = "popularity"
    COLLABORATIVE_FILTERING_ITEM_BASED = "collaborative_filtering_item_based"
    SEMANTIC_SIMILARITY = "semantic_similarity"

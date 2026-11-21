"""OPlague's early functional modules."""

from .impact import DIMENSIONS, PROFILES, get_profile, rank_profiles, search_profiles

__all__ = [
    "DIMENSIONS", "PROFILES", "get_profile", "rank_profiles", "search_profiles",
    "Candy", "CandyLine", "GiftPlan", "GreetingEdge", "allocate_equal",
    "allocate_weighted", "build_candy_basket", "build_greeting_graph",
    "combination_count", "percent_of", "plan_gift",
]


_GIFT_PLANNER_EXPORTS = {
    "Candy", "CandyLine", "GiftPlan", "GreetingEdge", "allocate_equal",
    "allocate_weighted", "build_candy_basket", "build_greeting_graph",
    "combination_count", "percent_of", "plan_gift",
}


def __getattr__(name: str):
    if name in _GIFT_PLANNER_EXPORTS:
        from . import gift_planner
        return getattr(gift_planner, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

"""OPlague's early functional modules."""

from .impact import DIMENSIONS, PROFILES, get_profile, rank_profiles, search_profiles
from .gift_planner import (
    Candy, CandyLine, GiftPlan, GreetingEdge, allocate_equal, allocate_weighted,
    build_candy_basket, build_greeting_graph, combination_count, percent_of, plan_gift,
)

__all__ = [
    "DIMENSIONS", "PROFILES", "get_profile", "rank_profiles", "search_profiles",
    "Candy", "CandyLine", "GiftPlan", "GreetingEdge", "allocate_equal",
    "allocate_weighted", "build_candy_basket", "build_greeting_graph",
    "combination_count", "percent_of", "plan_gift",
]

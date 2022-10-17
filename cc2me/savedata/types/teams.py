from .utils import ElementProxy, e_property, IntAttribute, BoolAttribute


class Team(ElementProxy):
    id = e_property(IntAttribute("id"))
    pattern_index = e_property(IntAttribute("pattern_index", default_value=5))
    is_ai_controlled = e_property(BoolAttribute("is_ai_controlled", default_value=False))
    is_neutral = e_property(BoolAttribute("is_neutral", default_value=False))
    is_destroyed = e_property(BoolAttribute("is_destroyed", default_value=False))
    currency = e_property(IntAttribute("currency", default_value=1500))
    start_tile_id = e_property(IntAttribute("start_tile_id"))

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from django.urls import reverse_lazy

from glom import T, glom
from glom.core import TType

from bing.config.models import BInGConfig

SUBSCRIPTIONS = set()


@dataclass
class Channel:
    name: str
    filters: Dict[str, Tuple[Any, TType]]

    def get_filters(self) -> dict:
        filters = {}
        for key, (target, spec) in self.filters.items():
            filters[key] = glom(target, spec)
        return filters


@dataclass
class Subscription:
    key: str
    url: str
    channels: List[Channel]

    def __post_init__(self):
        SUBSCRIPTIONS.add(self)

    def __hash__(self):
        return hash((self.key,))


AANVRAAG_ZAKEN = Subscription(
    key="aanvraag-zaken",
    url=reverse_lazy("callbacks-list"),
    channels=[
        Channel(
            name="zaken",
            filters={
                "bronorganisatie": (BInGConfig, T.get_solo().organisatie_rsin),
                "zaaktype": (BInGConfig, T.get_solo().zaaktype_aanvraag),
            },
        )
    ],
)

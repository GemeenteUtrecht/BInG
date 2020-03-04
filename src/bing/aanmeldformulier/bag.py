from django.conf import settings

import requests

BASE = "https://bag.basisregistraties.overheid.nl/api/v1/"


HEADERS = {"X-Api-Key": settings.BAG_API_KEY}


def get_panden():
    pass

from datetime import datetime, time
from typing import List, Tuple

from django.utils import timezone

from dateutil.relativedelta import relativedelta

from bing.config.models import BInGConfig
from bing.config.service import get_zrc_client

MEETING_DAY = 4  # Thursday in ISO standard
MEETING_FREQUENCY = "2 weeks"
MEETING_WEEKS = "odd"
MEETING_START_TIME = time(9, 0)
MEETING_END_TIME = time(12, 0)


def fetch_vergadering_zaken() -> List[dict]:
    """
    Retrieve all Zaken from vergadering-zaaktype.

    TODO: sort on API level
    TODO: include/exclude past zaken based on startdatum
    """
    config = BInGConfig.get_solo()
    zrc_client = get_zrc_client(scopes=["zds.scopes.zaken.lezen"])
    zaken = zrc_client.list(
        "zaak", query_params={"zaaktype": config.zaaktype_vergadering}
    )["results"]
    today = timezone.make_naive(timezone.now()).date().isoformat()
    zaken = [zaak for zaak in zaken if zaak["startdatum"] >= today]
    return sorted(zaken, key=lambda zaak: zaak["startdatum"])


def get_next_meeting(after=None) -> Tuple[datetime, datetime]:
    """
    Calculates the first upcoming meeting datetimes (start, end).

    Meetings are in odd weeks, biweekly.
    """
    _after = after or timezone.now()
    after = timezone.make_naive(_after)
    (year, week, day) = after.isocalendar()

    meeting_date = after.date()

    if day < MEETING_DAY:
        meeting_date += relativedelta(days=MEETING_DAY - day)
    else:
        meeting_date -= relativedelta(days=day - MEETING_DAY)

    # even week
    if (week % 2) == 0:
        meeting_date += relativedelta(weeks=1)
    elif day >= MEETING_DAY:  # we've past the meeting of this week
        meeting_date += relativedelta(weeks=2)

    start = datetime.combine(meeting_date, MEETING_START_TIME)
    end = datetime.combine(meeting_date, MEETING_END_TIME)

    return (timezone.make_aware(start), timezone.make_aware(end))

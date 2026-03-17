"""
======================================================
Limits the number of recommendations returned
by the API to the number specified. Can be used
to suppress a "More like this" tab.

e.g. test_limit_more_like_this_recs.py u:7734897822921774112 3
------------------------------------------------------
u: filter string to match in the url, e.g. a UUID
<int>: Number of recs to limit. Default is 0
======================================================
"""

from sky_mitm import (handle_response,
                      int_arg,
                      arg_regex_value,
                      get_regex,
                      allow_argument_fetching)
from sky_mitm.more_like_this import MoreLikeThisResponseModifier


def set_arguments(limit=None,
                  pattern=None):
    global LIMIT, PATTERN
    LIMIT = LIMIT if limit is None else limit
    PATTERN = PATTERN if pattern is None else get_regex(pattern)


if allow_argument_fetching():
    LIMIT = int_arg(default=0)
    PATTERN = arg_regex_value(key='u')
    set_arguments()


class LimitMoreLikeThisRecs(MoreLikeThisResponseModifier):

    def modify(self,
               body,
               limit=None,
               **_):
        body['recommendations'] = body['recommendations'][:limit]


def response(flow):
    modifiers = [LimitMoreLikeThisRecs(limit=LIMIT,
                                       pattern=PATTERN)]

    handle_response(flow=flow,
                    modifiers=modifiers)

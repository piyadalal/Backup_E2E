# encoding: utf-8

from __future__ import unicode_literals
from .base_stb_action import BaseStbAction, HEADING

CURRENCY = {'GBP': u'GBP',
            'EUR': u'EUR'}


class AssetsAvailableToPurchase(BaseStbAction):

    ACTION = "05348"

    HEADINGS = [{HEADING: "Offers"}]

    @property
    def purchase_options(self):
        return self.action.get('purchaseOptions', [])

    @staticmethod
    def purchase_offer_summary(offer_type,
                               offer):
        currency = offer.get('currency', '?')
        return (u"{offer_type} {media} {currency}{cost}"
                .format(offer_type=offer_type,
                        media=offer.get('media', '?'),
                        currency=CURRENCY.get(currency, currency),
                        cost=offer.get('cost')/100.0 if offer.get('cost') else '?'))

    @property
    def purchase_offers(self):
        return ([self.purchase_offer_summary(offer_type=self.purchase_options.get('offertype', '?'),
                                             offer=offer)
                 for offer in self.purchase_options.get('purchaseOffers', [])]
                if self.purchase_options else[])

    @property
    def rental_options(self):
        return self.action.get('rentalOptions', [])

    @staticmethod
    def rental_offer_summary(offer_type,
                             offer):
        currency = offer.get('currency', '?')
        return (u"{offer_type} {currency}{cost} {format}"
                .format(offer_type=offer_type,
                        currency=CURRENCY.get(currency, currency),
                        format=offer.get('format', '?'),
                        cost=offer.get('cost') / 100.0 if offer.get('cost') else '?'))

    @property
    def rental_offers(self):
        return ([self.rental_offer_summary(offer_type=self.rental_options.get('offertype', '?'),
                                           offer=offer)
                 for offer in self.rental_options.get('rentalOffers', [])]
                if self.rental_options else [])

    # ------------------------------------------------------------------------
    # Properties that map to headings...

    @property
    def offers(self):
        return '\n'.join(self.purchase_offers + self.rental_offers)

# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#          EBII MonsieurB <monsieurb@saaslys.com>
#          Sébastien BEAU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, api, fields

_logger = logging.getLogger(__name__)


class AccountProduct(models.Model):
    _inherit = 'keychain.account'

    namespace = fields.Selection(
        selection_add=[('roulier_geodis', 'Geodis')])

    def _roulier_geodis_init_data(self):
        return {'agencyId': '',
                'customerId': '',
                'is_test': True,
                'labelFormat': 'ZPL',
                'product': '',
                'model_id':''
                }

    @api.model
    def _reference_models(self):
        res = super(AccountProduct, self)._reference_models()
        res += [('delivery.carrier', 'Transporteur'),
                ('res_partner', 'Customer')]
        return res

    def _roulier_geodis_validate_data(self, data):
        # on aurait pu utiliser Cerberus ici
        # return 'agencyId' in data[service]
        # return 'shippingId' in data[service]
        # return 'customerId' in data[service]
        return True

class DeliveryCarrier(models.Model):
    _name = 'delivery.carrier'
    _inherit = [
        "abstract.account",
        "delivery.carrier",
    ]
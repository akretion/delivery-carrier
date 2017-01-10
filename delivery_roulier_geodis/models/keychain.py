# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#          EBII MonsieurB <monsieurb@saaslys.com>
#          Sébastien BEAU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields

_logger = logging.getLogger(__name__)


class AccountProduct(models.Model):
    _inherit = 'keychain.account'

    namespace = fields.Selection(
        selection_add=[('roulier_geodis', 'Geodis')])

    def _roulier_geodis_init_data(self):
        return {'agencyId': '',
                'customerId': '',
                'labelFormat': 'ZPL',
                'isTest': True,
                }

    def _roulier_geodis_validate_data(self, data):
        return True

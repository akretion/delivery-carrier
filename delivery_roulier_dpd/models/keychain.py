# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#          Sébastien BEAU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields

LAPOSTE_KEYCHAIN_NAMESPACE = 'roulier_dpd'


class AccountProduct(models.Model):
    _inherit = 'keychain.account'

    namespace = fields.Selection(
        selection_add=[(LAPOSTE_KEYCHAIN_NAMESPACE, 'Dpd')])

    def _roulier_laposte_init_data(self):
        return {
            "codeAgence": "",
            'is_test': True,
            'labelFormat': 'ZPL',
            }

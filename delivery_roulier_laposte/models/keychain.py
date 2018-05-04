# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#          Sébastien BEAU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields

_logger = logging.getLogger(__name__)

LAPOSTE_KEYCHAIN_NAMESPACE = 'roulier_laposte'


class KeychainAccount(models.Model):
    _inherit = 'keychain.account'

    namespace = fields.Selection(
        selection_add=[(LAPOSTE_KEYCHAIN_NAMESPACE, 'Laposte')])

    def _roulier_laposte_init_data(self):
        return {}

    def _roulier_laposte_validate_data(self, data):
        return True


class KeychainBackend(models.Model):
    _inherit = 'keychain.backend.roulier'
    _backend_name = 'roulier_laposte'

    namespace = fields.Selection(
        selection_add=[(LAPOSTE_KEYCHAIN_NAMESPACE, 'Laposte')])

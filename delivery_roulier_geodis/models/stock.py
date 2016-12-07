# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#          Sébastien BEAU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields, api
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

from datetime import datetime, timedelta


_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _geodis_get_shipping_date(self, package_id):
        """Estimate shipping date."""
        self.ensure_one()

        shipping_date = self.min_date
        if self.date_done:
            shipping_date = self.date_done

        shipping_date = datetime.strptime(
            shipping_date, DEFAULT_SERVER_DATETIME_FORMAT)

        tomorrow = datetime.now() + timedelta(1)
        if shipping_date < tomorrow:
            # don't send in the past
            shipping_date = tomorrow

        return shipping_date.strftime('%Y-%m-%d')

    @api.multi
    def _geodis_get_options(self, package):
        """Define options for the shippment.

        Like insurance, cash on delivery...
        It should be the same for all the packages of
        the shipment.
        """
        # should be extracted from a company wide setting
        # and oversetted in a view form
        self.ensure_one()
        options = self._roulier_get_options(package)
        import pdb; pdb.set_trace()
        return options

    @api.multi
    def _geodis_get_auth(self, package):
        """Fetch a laposte login/password.

        Currently it's global for the company.
        TODO:
            * allow multiple accounts
            * store the password securely
            * inject it via ENVIRONMENT variable
        """
        self.ensure_one()

        account = self._geodis_get_account()
        return {
            'login': account.login,
            'password': account.get_password()
        }

    def _geodis_get_account(self):
        accounts = self.env['keychain.account'].search(
            [['namespace', '=', 'roulier_geodis']])
        ##TODO demander de creer un compte dans Settings >keychain add
        return accounts[0]
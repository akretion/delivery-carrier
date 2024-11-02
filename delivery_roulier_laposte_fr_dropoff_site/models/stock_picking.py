#  @author Benoît Guillot <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _laposte_fr_get_receiver(self, package=None):
        receiver = super()._roulier_get_receiver(package=package)
        if self.final_shipping_partner_id:
            receiver = self.final_shipping_partner_id
        return receiver

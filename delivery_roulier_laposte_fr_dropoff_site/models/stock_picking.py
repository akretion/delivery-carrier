#  @author Benoît Guillot <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _roulier_convert_address(self, partner):
        address = super()._roulier_convert_address(partner)
        # mobile is mandatory for dropoff site delivery
        if self.final_shipping_partner_id and self.final_shipping_partner_id.mobile:
            address["mobilePhone"] = self.final_shipping_partner_id.mobile.replace(
                " ", ""
            )
        return address

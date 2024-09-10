#  @author Benoît Guillot <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    def _laposte_fr_get_parcel(self, picking):
        vals = super()._laposte_fr_get_parcel(picking)
        if picking.partner_id.is_dropoff_site:
            vals["pickupLocationId"] = picking.partner_id.ref
        return vals

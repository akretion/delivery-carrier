# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    geodis_cab = fields.Char(help="Barcode of the label")

    def _geodis_fr_parse_response(self, picking, response):
        res = self._roulier_parse_response(picking, response)
        i = 0
        for rec in self:
            rec.write(
                {
                    "geodis_cab": response["parcels"][i]["number"],
                    "parcel_tracking": picking.geodis_shippingid,
                }
            )
            i += 1
        return res

    def _geodis_fr_should_include_customs(self, picking):
        """Customs documents not implemented."""
        return False

    def _geodis_fr_get_tracking_link(self):
        return self.parcel_tracking_uri

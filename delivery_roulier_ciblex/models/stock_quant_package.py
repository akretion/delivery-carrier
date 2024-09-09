# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    def _ciblex_get_tracking_link(self):
        return (
            "https://secure.extranet.ciblex.fr/extranet/client/"
            "corps.php?module=colis&colis=%s" % self.parcel_tracking
        )

# © 2015 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


URL_TRACKING = "https://gls-group.eu/FR/fr/suivi-colis?match=%s"


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    carrier_id = fields.Many2one("delivery.carrier")

    def _gls_fr_rest_get_tracking_link(self):
        self.ensure_one()
        return URL_TRACKING % self.parcel_tracking

    def _gls_fr_rest_get_parcel(self, picking):
        vals = self._roulier_get_parcel(picking)
        # at the time, roulier do not set the product
        # if there is no services in the parcel
        # https://github.com/akretion/roulier/blob/master
        # /roulier/carriers/gls_fr/rest/encoder.py#L149
        if "services" not in vals.keys():
            vals["services"] = []
        return vals

# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from datetime import date

from odoo import fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


INCOTERM_MAPPING = {
    "DDP": "10",
    "DAP": "20",
}


class StockPicking(models.Model):
    _inherit = "stock.picking"

    carrier_tracking_ref = fields.Char(copy=False)

    def _gls_fr_rest_get_to_address(self, package=None):
        address = self._roulier_get_to_address(package=package)
        # TODO improve depending refactoring _roulier_convert_address()
        # specially keys: street2, company, phone, mobile
        addr = {}
        (
            addr["street"],
            addr["street2"],
            addr["street3"],
        ) = self.partner_id._get_split_address(3, 35)
        if "company" not in address:
            address["company"] = (
                self.partner_id.parent_id
                and self.partner_id.parent_id.name
                or self.partner_id.name
            )
        address["company"] = address["company"][:35]
        address["name"] = address["name"][:35]
        address["mobile"] = self.partner_id.mobile or self.partner_id.phone
        return address

    def _gls_fr_rest_get_service(self, account, package=None):
        result = self._roulier_get_service(account, package=package)
        gls_keys = ["carrier_gls_agency_id", "carrier_gls_customer_id"]
        config = {
            x.key: x.value
            for x in self.env["ir.config_parameter"].search([("key", "in", gls_keys)])
        }
        result.update({
            "agencyId": config.get("carrier_gls_agency_id", ""),
            "customerId": config.get("carrier_gls_customer_id", ""),
            "shippingId": self.name,
            "intructions": self.note or "",
            "consignee_ref": self.name[:20],
            "reference_1": self.origin[:20],
            "reference_2": self.name[:20],
        })
        incoterm_code = self._get_gls_incoterm()
        if incoterm_code:
            result["incoterm"] = incoterm_code
        return result

    def _get_gls_incoterm(self):
        self.ensure_one()
        incoterm = self.sale_id.incoterm
        gls_code = ""
        if incoterm:
            gls_code = INCOTERM_MAPPING.get(incoterm.code, "")
        return gls_code


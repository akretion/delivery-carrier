# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


INCOTERM_MAPPING = {
    "DDP": "10",
    "DAP": "20",
}

SHOPDELIVERYSERVICE = "shopDeliveryService"


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _gls_fr_rest_get_to_address(self, package=None):
        address = self._roulier_get_to_address(package=package)
        receiver = self._get_receiver(package=package)
        (
            address["street1"],
            address["street2"],
            address["street3"],
        ) = receiver._get_split_address(3, 35)
        # manage min/max size for company, name, contact (2-35)
        keys = ["name", "company", "contact"]
        for key in keys:
            size = len(address.get(key, ""))
            if size and size < 2:
                address[key] = ""
            if size and size > 35:
                address[key] = address[key][0:35]
        # For the shop delivery service the contact field is mandatory
        if self.carrier_id.code == SHOPDELIVERYSERVICE:
            address["contact"] = address["name"]
        return address

    def _gls_fr_rest_get_service(self, account, package=None):
        result = self._roulier_get_service(account, package=package)
        result.update(
            {
                # should probably renamed contactId in roulier
                "agencyId": account.gls_fr_rest_contact_id,
                "customerId": account.gls_fr_rest_customer_id,
                "intructions": self.note or "",
                "consignee_ref": self.name[:20],
                "reference1": self.origin and self.origin[:20] or self.name[:20],
                "reference2": self.name[:20] or "",
            }
        )
        incoterm_code = self._get_gls_incoterm()
        if incoterm_code:
            result["incoterm"] = incoterm_code
        # For consistency between GLS carrier codes the carrier code
        # is camelCase, however the product must not be
        if self.carrier_id.code == SHOPDELIVERYSERVICE:
            result["product"] = "shopdeliveryservice"
            result["pickupLocationId"] = self._get_gls_dropoff_site()
        return result

    def _get_gls_incoterm(self):
        self.ensure_one()
        incoterm = self.sale_id.incoterm
        gls_code = ""
        if incoterm:
            gls_code = INCOTERM_MAPPING.get(incoterm.code, "")
        return gls_code

    def _get_gls_dropoff_site(self):
        self.ensure_one()
        return self.partner_id.dropoff_site or ""

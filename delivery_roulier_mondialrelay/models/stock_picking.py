import logging

from odoo import models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def get_shipping_label_values(self, label):
        self.ensure_one()
        return {
            "name": "return_label-%s.pdf" % label.get("package_id", "?"),
            "res_id": self.id,
            "res_model": "stock.picking",
            "url": label["file"],
            "type": "url",
        }

    def _roulier_generate_return_label(self):
        self.ensure_one()
        result = self._roulier_generate_labels()[0]
        for label in result.get("labels", []):
            self.attach_shipping_label(label)

    def _mondialrelay_convert_address(self, partner):
        address = self._roulier_convert_address(partner)
        street1 = address["street1"]
        address_limit = 32

        # Prevent error on Mondial Relay API when street1 or street2 are too long
        if len(street1) > address_limit:
            address["street1"] = street1[:address_limit]
            # If street2 is empty, we put the rest of street1 in street2
            if not address.get("street2"):
                address["street2"] = street1[address_limit:]

        if len(address.get("street2", "")) > address_limit:
            address["street2"] = address["street2"][:address_limit]

        address["lang"] = partner.lang.split("_")[0].upper() if partner.lang else "EN"

        # Prevent unicode -> iso-8859-1 errors
        for key, value in address.items():
            if value:
                address[key] = value.encode("iso-8859-1", "ignore").decode("iso-8859-1")

        return address

    def _mondialrelay_get_sender(self, package=None):
        # In case of return we invert sender and receiver
        if self.carrier_code == "LCC":
            return self.partner_id
        else:
            return self.company_id.partner_id

    def _mondialrelay_get_receiver(self, package=None):
        # In case of return we invert sender and receiver
        if self.carrier_code == "LCC":
            return self.company_id.partner_id
        else:
            return self.partner_id

    def _mondialrelay_get_service(self, account, package=None):
        service = self._roulier_get_service(account, package)

        # We set it for now as auto pickup site
        service["pickupMode"] = "REL"
        service["pickupSite"] = "AUTO"
        service["pickupCountry"] = "XX"
        service["labelFormat"] = "PDF"
        service["shippingId"] = self.name
        service["customerId"] = self.partner_id.ref or str(self.partner_id.id)
        return service

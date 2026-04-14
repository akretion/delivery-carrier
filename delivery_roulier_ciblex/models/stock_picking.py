# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _ciblex_get_service(self, account, package=None):
        service = self._roulier_get_service(account, package=package)
        service.update(
            {
                "product": self.carrier_code,
                "customerId": account.ciblex_shipper_number,
                "logo": True,
            }
        )
        return service

    @api.model
    def _ciblex_convert_address(self, partner):
        address = self._roulier_convert_address(partner) or {}
        # Use get_split_adress from partner_helper module
        # to split the address on 4 lines
        streets = partner._get_split_address(4, 35)
        (
            address["street1"],
            address["street2"],
            address["street3"],
            address["street4"],
        ) = streets
        return address

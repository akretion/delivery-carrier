# Copyright 2023 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = "choose.delivery.carrier"

    @api.depends("partner_id")
    def _compute_available_carrier(self):
        super()._compute_available_carrier()
        for rec in self:
            prohibited_shipping_means_ids = rec.order_id.order_line.mapped(
                "prohibited_shipping_means_ids"
            )
            authorized_carriers = self.env["delivery.carrier"]
            for carrier in rec.available_carrier_ids:
                if not (
                    set(carrier.shipping_means_ids._origin)
                    & set(prohibited_shipping_means_ids)
                ):
                    authorized_carriers += carrier._origin
            rec.available_carrier_ids = authorized_carriers

# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from .roulier_helper import handled_carriers, metadata


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[(carrier, f"roulier.{carrier}") for carrier in handled_carriers],
        ondelete={carrier: "set default" for carrier in handled_carriers},
    )

    is_roulier = fields.Boolean(
        compute="_compute_is_roulier",
        store=True,
    )

    roulier_description = fields.Text(
        compute="_compute_roulier_description",
    )

    roulier_properties = fields.Properties(
        string="Carrier Properties",
        help="Properties for the carrier",
        definition="carrier_account_id.roulier_properties_definition",
    )

    @property
    def metadata(self):
        """Return the metadata for the current delivery type."""
        return metadata.get(self.delivery_type, {})

    @api.depends("delivery_type")
    def _compute_is_roulier(self):
        for record in self:
            record.is_roulier = record.delivery_type in handled_carriers

    def _compute_roulier_description(self):
        for record in self:
            if record.is_roulier:
                record.roulier_description = record.metadata.get("documentation", "")
            else:
                record.roulier_description = ""

    def _get_roulier_helper(self):
        return self.env["roulier.helper"].new({"carrier_id": self.id})

    def _roulier_rate_shipment(self, order):
        # TODO: Define an API at roulier level to get the price if available
        return {
            "success": True,
            "price": 0.0,
            "error_message": False,
            "warning_message": False,
        }

    def _roulier_send_shipping(self, pickings):
        helper = self._get_roulier_helper()

        res = []
        default_packaging_id = self.env["stock.package.type"].browse(
            self.roulier_properties.get("default_packaging_id", False)
        )
        for picking in pickings:
            packages = self._get_packages_from_picking(
                picking,
                default_packaging_id,
            )

            sender = picking.picking_type_id.warehouse_id.partner_id
            receiver = picking.partner_id

            result = helper.send_packages(packages, sender=sender, receiver=receiver)

            # Log a message along with the result attachments (labels, annexes)
            helper.attach_results(picking, result, packages)

            # Return the shipping data
            res.append(
                {
                    "exact_price": helper.extract_parcel_prices(result),
                    "tracking_number": helper.extract_parcel_tracking(result),
                }
            )
        return res

    def _roulier_get_tracking_link(self, tracking_number):
        helper = self._get_roulier_helper()
        tracking_link = helper.get_tracking_link(tracking_number)
        if tracking_link:
            return tracking_link

    def _roulier_cancel_shipment(self, picking):
        # TODO: Define an API at roulier level to cancel the shipment
        picking.carrier_tracking_ref = False
        labels = self.env["shipping.label"].search(
            [("res_id", "in", picking.ids), ("res_model", "=", "stock.picking")]
        )
        labels.mapped("attachment_id").unlink()

    def __getattr__(self, name):
        """
        Factorize individual roulier methods into a single method.

        Specific inheritance is done by overriding the _roulier_* methods and
        checking the delivery_type.
        """
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            for suffix in (
                "rate_shipment",
                "send_shipping",
                "get_tracking_link",
                "cancel_shipment",
            ):
                if name == f"{self.delivery_type}_{suffix}":
                    return getattr(self, f"_roulier_{suffix}")

            raise

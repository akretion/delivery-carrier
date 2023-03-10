from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("mondialrelay", "Mondialrelay")],
        ondelete={"mondialrelay": "set default"},
    )

    @api.depends("delivery_type")
    def _compute_can_generate_return(self):
        super()._compute_can_generate_return()

        for carrier in self:
            if carrier._is_roulier() and carrier.delivery_type == "mondialrelay":
                carrier.can_generate_return = True

    def mondialrelay_get_return_label(self, pickings, tracking_number, origin_date):
        if not pickings.package_ids:
            raise UserError(_("You must have at least one package"))
        pickings._roulier_generate_return_label()

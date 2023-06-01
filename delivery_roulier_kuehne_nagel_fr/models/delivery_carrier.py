# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("kuehne_nagel_fr", "Kuehne+Nagel")],
        ondelete={"kuehne_nagel_fr": "set default"},
    )
    kuehne_delivery_mode = fields.Selection(
        [("D", "Direct Delivery"), ("R", "Appointment")], "Delivery Type", default="R"
    )

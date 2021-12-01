# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CarrierAccount(models.Model):
    _inherit = "carrier.account"

    def complete_gls_settings(self):
        domain = (
            self.env.ref(
                "delivery_roulier_gls_fr." "delivery_carrier_gls_agency_id"
            ).id,
            self.env.ref(
                "delivery_roulier_gls_fr." "delivery_carrier_gls_customer_id"
            ).id,
        )
        return {
            "name": "GLS settings",
            "type": "ir.actions.act_window",
            "views": [[False, "list"], [False, "form"]],
            "res_model": "ir.config_parameter",
            "domain": [["id", "in", domain]],
        }

    gls_fr_rest_file_format = fields.Selection(
        selection=[
            ("PDF", "PDF"),
            ("ZPL", "ZPL"),
            ("PNG", "PNG"),
        ],
        string="GLS File Format",
        help="Default format of the carrier's label you want to print",
    )

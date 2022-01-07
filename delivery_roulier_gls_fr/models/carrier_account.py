# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CarrierAccount(models.Model):
    _inherit = "carrier.account"

    gls_fr_rest_customer_id = fields.Char(string="Gls Customer ID")
    gls_fr_rest_contact_id = fields.Char(string="GLS Contact ID")
    gls_fr_rest_file_format = fields.Selection(
        selection=[
            ("PDF", "PDF"),
            ("ZPL", "ZPL"),
            ("PNG", "PNG"),
        ],
        string="GLS File Format",
        help="Default format of the carrier's label you want to print",
    )

# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class CarrierAccount(models.Model):
    _inherit = "carrier.account"

    ciblex_shipper_number = fields.Char()
    ciblex_file_format = fields.Selection(
        selection=[
            ("PDF", "PDF"),
            ("EPL", "EPL"),
            ("ZPL", "ZPL"),
        ],
        string="Ciblex File Format",
        help="Default format of the carrier's label you want to print",
    )

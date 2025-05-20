# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    carrier_id = fields.Many2one("delivery.carrier", string="Carrier")
    parcel_tracking = fields.Char()

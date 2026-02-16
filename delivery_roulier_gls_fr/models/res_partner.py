# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    dropoff_site = fields.Char(
        help="Carrier-specific drop-off site identifier. "
        "Used when this partner location serves as a pickup point.",
    )

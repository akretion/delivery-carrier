# Copyright 2023 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    shipping_means_ids = fields.Many2many(
        comodel_name="delivery.carrier.typology",
        string="Shipping means",
    )


class DeliveryCarrierTypology(models.Model):
    _name = "delivery.carrier.typology"
    _description = "Shipping means"

    name = fields.Char(string="Name", required=True, translate=True)
    code = fields.Char(string="Code")
    description = fields.Char(string="Description", translate=True)
    company_id = fields.Many2one("res.company", string="Company")

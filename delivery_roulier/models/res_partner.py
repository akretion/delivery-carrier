# coding: utf-8
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    dropoff_site_number = fields.Char(
        help='the number used by the carrier to identify the dropoff site'
    )

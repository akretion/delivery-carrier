# coding: utf-8
# © 2016 Raphael Reverdy @ Akretion <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    keychain_account = fields.Many2one(
        comodel_name='keychain.account',
        string="Keychain Account"
    )

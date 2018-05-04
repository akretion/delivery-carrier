# -*- coding: utf-8 -*-
# Copyright 2018 Akretion (http://www.akretion.com).
# @author Raphael Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class KeychainBackendRoulier(models.Model):
    _name = 'keychain.backend.roulier'
    _inherit = 'keychain.backend'

    namespace = fields.Selection([])

    # TODO: move it in keychainbackend ?
    login = fields.Char(
        compute="_compute_login",
        inverse="_inverse_login",
        required=True)

    @api.multi
    def _inverse_login(self):
        for record in self:
            account = self._get_keychain_account()
            if record.login:
                account.login = record.login

    @api.multi
    def _compute_login(self):
        for record in self:
            account = record._get_existing_keychain()
            if account and account.login:
                record.login = account.login

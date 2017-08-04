# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2016 Akretion (https://www.akretion.com).
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#          Sébastien BEAU
##############################################################################

from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    directional_code_id = fields.Many2one(
        comodel_name="kuehne.directional.code",
        string="Directional code")

    @api.multi
    def action_button_confirm(self):
        """
        Set the route montage in case of assembled products
        Send mail to the customer when confirm
        """
        self.ensure_one()
        res = super(SaleOrder, self).action_button_confirm()
        tmp = 'delivery_roulier_kuehne_nagel.missing_directional_code_template'
        if not self.directional_code_id:
            email_template = self.env.ref(tmp)
            email_template.send_mail(self.id)
        return res

    @api.multi
    def onchange_delivery_id(
            self, company_id, partner_id, delivery_id, fiscal_position):
        res = super(SaleOrder, self).onchange_delivery_id(
            company_id, partner_id, delivery_id, fiscal_position)
        directional_code_obj = self.env['kuehne.directional.code']
        if delivery_id:
            partner = self.env['res.partner'].browse(delivery_id)
            if not partner.zip:
                return res
            code = directional_code_obj._search_directional_code(
                self.company_id.country_id.id,
                partner.country_id.id,
                partner.zip,
                partner.city
            )
            if code and len(code) == 1:
                res['value']['directional_code_id'] = code.id
        return res

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
        if not self.directional_code_id and self.carrier_id.type == 'kuehne':
            self.send_missing_directional_code_email()
        return res

    @api.multi
    def send_missing_directional_code_email(self):
        self.ensure_one()
        tmp = 'delivery_roulier_kuehne_nagel.missing_directional_code_template'
        email_template = self.env.ref(tmp)
        email_template.send_mail(self.id)

    @api.multi
    def write(self, vals):
        # send mail for all sale orders if new carrier is kuehne and old one was not
        # if the directional_code_id is not set.
        orders_to_notify = self.env["sale.order"]
        if vals.get("carrier_id"):
            new_carrier = self.env["delivery.carrier"].browse(vals["carrier_id"])
            if new_carrier.type == "kuehne":
                orders_to_notify = self.filtered(
                    lambda so: so.carrier_id.type != 'kuehne' and not so.directional_code_id and so.state in ("progress", "manual"))
        res = super(SaleOrder, self).write(vals)
        for order_to_notify in orders_to_notify:
            order_to_notify.send_missing_directional_code_email()
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

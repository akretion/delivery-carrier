# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2014 Akretion (http://www.akretion.com).
#  @author David BEAL <david.beal@akretion.com>
#          Yannick VAUCHER, Camptocamp SA
#
##############################################################################

from openerp import models, fields
from openerp import api


class KuehneNagelConfigSettings(models.TransientModel):
    _name = 'kuehne.nagel.config.settings'
    _inherit = 'res.config.settings'

    warehouse_id = fields.Many2one(
        'stock.warehouse', 'Warehouse', required=True)
    kuehne_office_name = fields.Char(related='warehouse_id.kuehne_office_name')
    kuehne_office_code = fields.Char(related='warehouse_id.kuehne_office_code')
    kuehne_office_country_id = fields.Many2one(
        related='warehouse_id.kuehne_office_country_id',
        comodel_name="res.country")
    kuehne_goods_name = fields.Char(related='warehouse_id.kuehne_goods_name')
    kuehne_siret = fields.Char(related='warehouse_id.kuehne_siret')
    kuehne_delivery_contract = fields.Selection(
        related='warehouse_id.kuehne_delivery_contract')
    kuehne_service_system = fields.Selection(
        related='warehouse_id.kuehne_service_system')
    kuehne_shipping_config = fields.Selection(
        related='warehouse_id.kuehne_shipping_config')
    kuehne_vat_config = fields.Selection(
        related='warehouse_id.kuehne_vat_config')
    kuehne_invoicing_contract = fields.Char(
        related='warehouse_id.kuehne_invoicing_contract')
    kuehne_label_logo = fields.Text(related='warehouse_id.kuehne_label_logo')
    kuehne_tracking_url = fields.Char(
        related='warehouse_id.kuehne_tracking_url')
    kuehne_sender_id = fields.Char(
        related='warehouse_id.kuehne_sender_id')

    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        if not self.warehouse_id:
            return
        warehouse_id = self.warehouse_id
        self.kuehne_siret = warehouse_id.kuehne_siret
        self.kuehne_office_name = warehouse_id.kuehne_office_name
        self.kuehne_office_code = warehouse_id.kuehne_office_code
        self.kuehne_office_country_id = warehouse_id.kuehne_office_country_id
        self.kuehne_goods_name = warehouse_id.kuehne_goods_name
        self.kuehne_delivery_contract = warehouse_id.kuehne_delivery_contract
        self.kuehne_service_system = warehouse_id.kuehne_service_system
        self.kuehne_shipping_config = warehouse_id.kuehne_shipping_config
        self.kuehne_vat_config = warehouse_id.kuehne_vat_config
        self.kuehne_invoicing_contract = warehouse_id.kuehne_invoicing_contract
        self.kuehne_label_logo = warehouse_id.kuehne_label_logo
        self.kuehne_tracking_url = warehouse_id.kuehne_tracking_url
        self.kuehne_sender_id = warehouse_id.kuehne_sender_id

# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2016 Akretion (http://www.akretion.com).
#  @author Benoît GUILLOt <benoit.guillot@akretion.com>
#
##############################################################################

from openerp import models, fields


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    kuehne_siret = fields.Char('Kuehne Siret')
    kuehne_office_name = fields.Char('Kuehne Nagel Office Name')
    kuehne_office_country_id = fields.Many2one(comodel_name="res.country", string='Kuehne Nagel Office Country')
    kuehne_office_code = fields.Char('Kuehne Nagel Office Code')
    kuehne_goods_name = fields.Char('Kuehne Nagel Goods Name')
    kuehne_delivery_contract = fields.Selection([('gsp', 'KN EuroLink First'), ('gfx', 'KN EuroLink Fix')], string="Delivery contract")
    kuehne_service_system = fields.Selection([('3', 'Parcel service'), ('9', 'Chartering')], string="Service system", default='3')
    kuehne_shipping_config = fields.Selection([('p', 'Paid shipping cost'), ('c', 'Own shipping cost'), ('f', 'Service')], string="Shipping")
    kuehne_vat_config = fields.Selection([('v', 'VAT payable'), ('e', 'VAT exempt')], string="VAT")
    kuehne_invoicing_contract = fields.Char(string="Invoicing contract number")

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

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    kuehne_meta = fields.Text(
        "meta",
        help="Needed for deposit slip",
    )
    kuehne_meta_footer = fields.Text(
        "meta footer",
        help="Needed for deposit slip",
    )
    kuehne_delivery_type = fields.Selection([
        ('d', 'Direct Delivery'),
        ('r', 'Appointment')],
        'Delivery Type',
        default='r')

    @api.multi
    def kuehne_get_meta(self):
        self.ensure_one()
        parcels = self._get_packages_from_picking().kuehne_get_meta()
        meta = '%s\n%s\n%s' % (
            self.kuehne_meta, parcels, self.kuehne_meta_footer)
        return meta

    def _kuehne_get_directional_code(self):
        directional_code = False
        directional_code_obj = self.env['kuehne.directional.code']
        if self.sale_id and self.sale_id.directional_code_id:
            directional_code = self.sale_id.directional_code_id
        else:
            directional_code = directional_code_obj._search_directional_code(
                self.company_id.country_id.id,
                self.partner_id.country_id.id,
                self.partner_id.zip,
                self.partner_id.city
                )
        if not directional_code:
            raise UserError(
                _('No directional code found for the picking %s !' % self.id))
        return {
            'office': directional_code.office_code,
            'round': directional_code.office_round,
            'export_hub': directional_code.export_hub
        }

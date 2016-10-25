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

from openerp.tools.config import config
from openerp import models, fields, api

from base64 import b64encode
from roulier import roulier
import itertools
from datetime import datetime


class DepositSlip(models.Model):
    _inherit = "deposit.slip"

    @api.multi
    def _kuehne_create_edi_data(self):
        now = datetime.now()
        date = now.date().strftime('%y%m%d')
        hour = now.time().strftime('%H%M')
        warehouse = self.picking_type_id.warehouse_id
        data = {
            'service': {
                'date': date,
                'hour': hour,
                'depositNumber': self.name,
                'deliveryContract': warehouse.kuehne_delivery_contract,
                'shippingConfig': warehouse.kuehne_shipping_config.upper(),
                'vatConfig': warehouse.kuehne_vat_config.upper(),
                'invoicingContract': warehouse.kuehne_invoicing_contract,
                'serviceSystem': warehouse.kuehne_service_system,
                'goodsName': warehouse.kuehne_goods_name,
                'lines': self._kuehne_create_edi_lines(),
                'lineNumber': self._kuehne_get_line_number(),
            },
            'from_address': {
                "number": self.company_id.siren,
                "siret": self.company_id.siret,
                "name": self.company_id.name,
            },
            'to_address': {
                "number": warehouse.kuehne_siret[:9],
                "siret": warehouse.kuehne_siret,
                "name": warehouse.kuehne_office_name,
            }
        }
        return data

    @api.multi
    def _kuehne_get_line_number(self):
        """Get the number of lines of the deposit slip.
        @returns int
        """
        self.ensure_one()
        lines = 14
        for picking in self.picking_ids:
            lines += 17
            lines += len(picking._get_packages_from_picking())
        return lines

    @api.multi
    def _kuehne_create_edi_lines(self):
        """Create lines for each picking.
        The carrier is expecting a line per shipping.
        @returns []
        """
        self.ensure_one()
        lines = []
        for picking in self.picking_ids:
            lines.append(picking.kuehne_get_meta())
        return lines

    @api.multi
    def _kuehne_create_edi_file(self):
        """Create a .txt file with headers and data.
        params:
            data : [OrderedDict]
        return: io.ByteIO
        """
        data = self._kuehne_create_edi_data()
        kuehne = roulier.get('kuehne')
        txt = kuehne.get_deposit_slip(data)  # io.ByteIO
        return txt

    @api.multi
    def _kuehne_create_attachment(self):
        """Create a slip and add it in attachment."""
        edi_file = self._kuehne_create_edi_file()
        vals = {
            'name': self.name,
            'res_id': self.id,
            'res_model': 'deposit.slip',
            'datas': b64encode(edi_file.encode('utf-8')),
            'datas_fname': '%s.txt' % self.name,
            'type': 'binary',
            'task_id': self.env.ref('delivery_roulier_kuehne_nagel.kuehne_nagel_export_deposit_task').id,
            'file_type': 'export_external_location'
        }
        return self.env['ir.attachment.metadata'].create(vals)

    @api.multi
    def create_edi_file(self):
        self.ensure_one()
        if self.carrier_type == 'kuehne':
            return self._kuehne_create_attachment()
        else:
            return super(DepositSlip, self).create_edi_file()

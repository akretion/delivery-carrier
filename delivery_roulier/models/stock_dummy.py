# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2016 Akretion (https://www.akretion.com).
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#
##############################################################################
from openerp import models


class StockPackage(models.Model):
    _inherit = 'stock.quant.package'

    def _dummy_before_call(self, picking_id, request):
        request['parcel']['reference'] = (
            "%s/%s" % (
                picking_id, len(picking_id._get_packages_from_picking())
            )
        )
        return request

    def _dummy_after_call(self, picking_id, response):
        return [{
            "data": response['zpl'],
            "tracking_id": "",
            "name": picking_id.name,
        }]

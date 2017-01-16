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
from openerp.exceptions import Warning as UserError
from openerp.tools.translate import _


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    kuehne_meta = fields.Text(
        "meta",
        help="Needed for deposit slip",
    )

    @api.model
    def _get_tracking_url(self, picking):
        res = super(StockQuantPackage, self)._get_tracking_url(picking)
        if picking.carrier_id.type == 'kuehne':
            if not picking.carrier_tracking_ref:
                raise UserError(_('No tracking reference for the delivery %s' % picking.name))
            res = "https://espace-services.kuehne-nagel-road.fr/redirect.aspx?IdExpediteur=%s&RefExpediteur=%s" % (
                picking.picking_type_id.warehouse_id.kuehne_invoicing_contract, picking.carrier_tracking_ref)
        return res

    @api.multi
    def kuehne_get_meta(self):
        return '\n'.join([pack.kuehne_meta for pack in self])

    def _kuehne_before_call(self, picking, request):
        directional_code = picking._kuehne_get_directional_code()
        warehouse = picking.picking_type_id.warehouse_id
        office_name = "KUEHNE NAGEL ROAD / AG : %s %s %s" % (
            warehouse.kuehne_office_country_id.code.upper(),
            warehouse.kuehne_office_code,
            warehouse.kuehne_office_name)
        sender_name = "%s/%s/%s/%s" % (
            picking.company_id.name,
            picking.company_id.country_id.code.upper(),
            picking.company_id.zip,
            picking.company_id.city)
        map_delivery_contract = {
            'gsp': 'F',
            'gfx': 'D',
        }
        label_delivery_contract = map_delivery_contract.get(warehouse.kuehne_delivery_contract, 'C')
        if picking.date_done:
            shipping_date = fields.Date.from_string(picking.date_done)
        else:
            shipping_date = fields.Date.from_string(fields.Date.today())
        request.update({
            'service': {
                'shippingDate': shipping_date.strftime('%y%m%d'),
                'labelShippingDate': shipping_date.strftime('%d/%m/%y'),
                'goodsName': warehouse.kuehne_goods_name,
                'epalQuantity': 0,
                'shippingOffice': directional_code['office'],
                'shippingRound': directional_code['round'],
                'shippingName': picking.name.replace('/', '-'),
                'mhuQuantity': len(picking._get_packages_from_picking()),
                'weight': picking.weight,
                'volume': picking.volume,
                'deliveryContract': warehouse.kuehne_delivery_contract and warehouse.kuehne_delivery_contract.upper() or '',
                'labelDeliveryContract': label_delivery_contract,
                'exportHub': directional_code['export_hub'],
                'orderName': picking.sale_id.name,
                'shippingConfig': warehouse.kuehne_shipping_config.upper(),
                'vatConfig': warehouse.kuehne_vat_config.upper(),
                'invoicingContract': warehouse.kuehne_invoicing_contract,
                'deliveryType': picking.kuehne_delivery_type.upper(),
                'serviceSystem': warehouse.kuehne_service_system,
                'note': picking.note and picking.note or '',
                'kuehneOfficeName': office_name
            }
        })
        request['to_address']['contact'] = picking.partner_id.name
        request['from_address']['company'] = sender_name
        package_ids = picking._get_packages_from_picking().ids
        package_ids.sort()
        count = 1
        for pack_id in package_ids:
            if pack_id == self.id:
                break
            count += 1
        request['parcel'].update({
            'barcode': self.name,
            'number': count
        })
        return request

    def _kuehne_after_call(self, picking, response):
        self.kuehne_meta = response['parcel']
        self.parcel_tracking = response['parcelNumber']
        picking.kuehne_meta = response['line']
        picking.kuehne_meta_footer = response['footer']
        picking.carrier_tracking_ref = response['trackingNumber']
        return {
            "data": response['zpl'],
            "name": self.name,
        }


    @api.model
    def _kuehne_error_handling(self, payload, response):
        ret_mess = 'Erreur!'
        if response.get('api_call_exception'):
            # InvalidInputException
            # on met des clés plus explicites vis à vis des objets odoo
            suffix = (u"\nSignification des clés dans le contexte Odoo:\n"
                      u"- 'to_address' correspond à 'adresse client'\n"
                      u"- 'from_address' correspond à 'adresse de la société'")
            message = u'Données transmises:\n%s\n\nExceptions levées%s\n%s' % (
                payload, response, suffix)
            return message
        return ret_mess

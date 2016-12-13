# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#           EBII MonsieurB <monsieurb@saaslys.com>
#          Sébastien BEAU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import _, api, models
import logging

_logger = logging.getLogger(__name__)


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    def _geodis_before_call(self, picking, request):
        # def calc_package_price():
        #     return sum(
        #         [op.product_id.list_price * op.product_qty
        #             for op in self.get_operations()]
        #     )
        # TODO _get_options is called fo each package by the result
        # is the same. Should be store after first call
        # chercher key chain

        # import pdb; pdb.set_trace()
        account = picking._get_account(self)
        service = account.get_data()
        request['service']['customerId'] = service['customerId']
        request['service']['agencyId'] = service['agencyId']
        # TODO passer contexte multi compagny ou multi compte à la sequence"
        shp = self._get_colis_id()
        _logger.warning('shp: %s', (shp))
        request['service']['shippingId'] = shp
        # _logger.warning("request : %s", (request) )
        # _logger.warning("request %s", (request))
        return request

    def _geodis_after_call(self, picking, response):
        # import pdb; pdb.set_trace()
        custom_response = {
            'name': response['barcode'],
            'data': response.get('label'),
        }
        if response.get('url'):
            custom_response['url'] = response['url']
            custom_response['type'] = 'url'
        self.parcel_tracking = response['barcode']
        return custom_response

    @api.model
    def _geodis_error_handling(self, payload, response):
        payload['auth']['password'] = '****'
        if 'Input error ' in response:
            # InvalidInputException
            # on met des clés plus explicites vis à vis des objets odoo
            suffix = (
                u"\nSignification des clés dans le contexte Odoo:\n"
                u"- 'to_address' : adresse du destinataire (votre client)\n"
                u"- 'from_address' : adresse de l'expéditeur (vous)")
            message = u'Données transmises:\n%s\n\nExceptions levées %s' \
                      u'\n%s' % (payload, response, suffix)
            return message
        elif 'message' in response:
            message = u'Données transmises:\n%s\n\nExceptions levées %s\n' \
                      u'cat ' % (payload, response)
            return message
        elif response['status'] == 'error':
            message = u'Données transmises:\n%s\n\nExceptions levées %s\n' \
                      u'cat ' % (payload, response)
            return message
        else:
            message = "Error Unknown"
            return message

    @api.model
    def format_one_exception(self, message, map_responses):
        param_message = {
            'ws_exception':
                u'%s\n' % message['message'],
            'resolution': u''}
        if message and message.get('id') in map_responses.keys():
            param_message['resolution'] = _(u"Résolution\n-------------\n%s" %
                                            map_responses[message['id']])
        return _(u"Réponse de Geodis:\n"
                 u"%(ws_exception)s\n%(resolution)s"
                 % param_message)

    @api.multi
    def _get_colis_id(self):
        sequence = self.env['ir.sequence'].next_by_code("geodis.nrecep.number")
        # this is prefixe by year_ so split it for use in shp: info
        list = sequence.split('_')
        # start by many zero so stringyfy before return to keep 8digits
        return str(list[1])
# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#           EBII MonsieurB <monsieurb@saaslys.com>
#          Sébastien BEAU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import _, api, models
from .stock import StockPicking
import logging
import json

_logger = logging.getLogger(__name__)

class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    def _geodis_before_call(self, picking, request):
        def calc_package_price():
            return sum(
                [op.product_id.list_price * op.product_qty
                    for op in self.get_operations()]
            )
        # TODO _get_options is called fo each package by the result
        # is the same. Should be store after first call
        #chercher key chain
        account = self._geodis_get_account()
        service = json.loads(account.data)
        import pdb;pdb.set_trace()
        request['service']['customerId']= service['customerId']
        request['service']['agencyId']= service['agencyId']
        sequence = self.env['ir.sequence'].next_by_code("geodis.nrecep.number")
        #this is prefixe by year_ so split it for use in shp: info
        shp = sequence.split('_')
        request['service']['shippingId']=str(shp[1])
        _logger.warning("request : %s",(request) )
        # appelé la sequence
        return request

    def _geodis_after_call(self, picking, response):
        # CN23 is included in the pdf url
        import pdb; pdb.set_trace()
        custom_response = {
            'name': response['parcelNumber'],
            'data': response.get('label'),
        }
        if response.get('url'):
            custom_response['url'] = response['url']
            custom_response['type'] = 'url'
        self.parcel_tracking = response['parcelNumber']
        return custom_response

    @api.multi
    def _geodis_get_account(self):
        accounts = self.env['keychain.account'].search(
            [['namespace', '=', 'roulier_geodis']])
        ##TODO demander de creer un compte dans Settings >keychain add
        return accounts[0]
    @api.multi
    def _geodis_get_customs(self, picking):
        """ see _roulier_get_customs() docstring
        """
        customs = self._roulier_get_customs(picking)
        return customs

    @api.multi
    def _geodis_should_include_customs(self, picking):

        return False

    @api.model
    def _geodis_error_handling(self, payload, response):
        payload['auth']['password'] = '****'
        ret_mess = ''
        #if keychain service values is with empty data or error messagage response si string
        import pdb; pdb.set_trace()
        rep={}
        if type(response) == type(dict()):

            rep = response
        else:
            rep = json.loads(response)

        if rep.has_key('Input error '):
            # InvalidInputException
            # on met des clés plus explicites vis à vis des objets odoo
            suffix = (
                u"\nSignification des clés dans le contexte Odoo:\n"
                u"- 'to_address' : adresse du destinataire (votre client)\n"
                u"- 'from_address' : adresse de l'expéditeur (vous)")
            message = u'Données transmises:\n%s\n\nExceptions levées %s\n%s' % (
                payload, response, suffix)
            return message
        elif rep.has_key('message'):
            message = u'Données transmises:\n%s\n\nExceptions levées %s\ncat ' % (
                payload, response)
            return message
        elif response.get('messages'):
            # Webservice error
            # on contextualise les réponses ws aux objets Odoo
            map_responses = {
                30204:
                    u"La 2eme ligne d'adresse du client partenaire "
                    u"est vide ou invalide",
                30221:
                    u"Le telephone du client ne doit comporter que des "
                    u"chiffres ou le symbole +: convertissez tous vos N° de "
                    u"telephone au format standard a partir du menu suivant:\n"
                    u"Configuration > Technique > Telephonie > Reformate "
                    u"les numeros de telephone ",
                30100:
                    u"La seconde ligne d'adresse de l'expéditeur est "
                    u"vide ou invalide.",
            }
            parts = []
            request = response['response'].request.body
            if self._uid > 1:
                request = '%s<password>****%s' % (
                    request[:request.index('<password>')],
                    request[request.index('</password>'):])
            for message in response.get('messages'):
                parts.append(self.format_one_exception(message, map_responses))
            ret_mess = _(u"Incident\n-----------\n%s\n"
                         u"Données transmises:\n"
                         u"-----------------------------\n%s") % (
                u'\n'.join(parts), request.decode('utf-8'))
        return ret_mess

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

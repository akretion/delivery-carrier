# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#          Sébastien BEAU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import _, api, models

CUSTOMS_MAP = {
    'gift': 1,
    'sample': 2,
    'commercial': 3,
    'document': 4,
    'other': 5,
    'return': 6,
}


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    def _laposte_before_call(self, picking, request):
        def calc_package_price():
            return sum(
                [op.product_id.list_price * op.product_qty
                    for op in self.get_operations()]
            )
        # TODO _get_options is called fo each package by the result
        # is the same. Should be store after first call
        request['parcel'].update(picking._laposte_get_options(self))
        if request['parcel'].get('COD'):
            request['parcel']['codAmount'] = self._get_cash_on_delivery(
                picking)
        request['service']['totalAmount'] = '%.f' % (  # truncate to string
            calc_package_price() * 100  # totalAmount is in centimes
        )
        request['service']['transportationAmount'] = 10  # how to set this ?
        request['service']['returnTypeChoice'] = 3  # do not return to sender
        request['to_address']['phone'] = '+33667228689'
        return request

    def _laposte_after_call(self, picking, response):
        # CN23 is included in the pdf url
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
    def _laposte_get_customs(self, picking):
        """ see _roulier_get_customs() docstring
        """
        customs = self._roulier_get_customs(picking)
        customs['category'] = CUSTOMS_MAP.get(picking.customs_category)
        return customs

    @api.multi
    def _laposte_should_include_customs(self, picking):
        """Choose if customs infos should be included in the WS call.

        Return bool
        """
        # Customs declaration (cn23) is needed when :
        # dest is not in UE
        # dest is attached territory (like Groenland, Canaries)
        # dest is is Outre-mer
        #
        # see https://boutique.laposte.fr/_ui/doc/formalites_douane.pdf
        # Return true when not in metropole.
        international_products = (
            'COM', 'CDS',  # outre mer
            'COLI', 'CORI',  # colissimo international
            'BOM', 'BDP', 'BOS', 'CMT',  # So Colissimo international
        )
        return picking.carrier_code.upper() in international_products

    @api.model
    def _laposte_error_handling(self, payload, response):
        payload['auth']['password'] = '****'
        ret_mess = ''
        if response.get('api_call_exception'):
            # InvalidInputException
            # on met des clés plus explicites vis à vis des objets odoo
            suffix = (u"\nSignification des clés dans le contexte Odoo:\n"
                      u"- 'to_address' correspond à 'adresse client'\n"
                      u"- 'from_address' correspond à 'adresse de la société'")
            message = u'Données transmises:\n%s\n\nExceptions levées%s\n%s' % (
                payload, response, suffix)
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
        return _(u"Réponse de Laposte:\n"
                 u"%(ws_exception)s\n%(resolution)s"
                 % param_message)

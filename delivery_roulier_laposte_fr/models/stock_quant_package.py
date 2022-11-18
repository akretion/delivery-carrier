#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import _, api, models

_logger = logging.getLogger(__name__)


CUSTOMS_MAP = {
    "gift": 1,
    "sample": 2,
    "commercial": 3,
    "document": 4,
    "other": 5,
    "return": 6,
}


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    def _laposte_fr_get_parcel(self, picking):
        vals = self._roulier_get_parcel(picking)

        # name is missleading, it is actually the cost of the transport which
        # is expected here.
        carrier_sale_line = picking.sale_id.order_line.filtered(lambda line: line.is_delivery)
        # put 1 in no shipping fee in so because it is mandatory to have some value.
        # and we have no other way to the real cost
        shipping_cost = carrier_sale_line.price_subtotal or 1.0
        vals["totalAmount"] = "%.f" % (  # truncate to string
            shipping_cost * 100  # totalAmount is in centimes
        )
        vals.update(picking._laposte_fr_get_options(self))
        if vals.get("COD"):
            vals["codAmount"] = self._get_cash_on_delivery(picking)

        if self._should_include_customs(picking):
            vals["customs"] = self._get_customs(picking)
        return vals

    def _laposte_fr_get_customs(self, picking):
        """see _roulier_get_customs() docstring"""
        customs = self._roulier_get_customs(picking)
        customs["category"] = CUSTOMS_MAP.get(picking.customs_category)
        return customs

    def _laposte_fr_should_include_customs(self, picking):
        """Choose if customs infos should be included in the WS call.

        Return bool
        """
        # Customs declaration (cn23) is needed when :
        # dest is not in UE
        # dest is attached territory (like Groenland, Canaries)
        # dest is is Outre-mer
        #
        # If origin is not France metropole, this implementation may be wrong.
        # see https://boutique.laposte.fr/_ui/doc/formalites_douane.pdf
        europe_group = self.env.ref("base.europe")
        eu_country_ids = europe_group.country_ids.ids
        sender_is_intrastat = picking._get_sender(self).country_id.id in eu_country_ids
        receiver_is_intrastat = (
            picking._get_receiver(self).country_id.id in eu_country_ids
        )
        if sender_is_intrastat:
            if receiver_is_intrastat:
                return False  # national or within UE
            else:
                return True  # internationnal shipping
        else:
            _logger.warning("Customs may be not needed for picking %s" % picking.id)
            return True

    @api.model
    def _laposte_fr_invalid_api_input_handling(self, payload, exception):
        payload["auth"]["password"] = "****"
        response = str(exception)
        suffix = (
            "\nSignification des clés dans le contexte Odoo:\n"
            "- 'to_address' : adresse du destinataire (votre client)\n"
            "- 'from_address' : adresse de l'expéditeur (vous)"
        )
        message = "Données transmises:\n{}\n\nExceptions levées{}\n{}".format(
            payload,
            response,
            suffix,
        )
        return message

    def _laposte_fr_carrier_error_handling(self, payload, exception):
        response = exception.response
        request = response.request.body.decode()

        if self._uid > 2:
            # rm pwd from dict and xml
            payload["auth"]["password"] = "****"
            request = "{}<password>****{}".format(
                request[: request.index("<password>")],
                request[request.index("</password>") :],
            )

        # Webservice error
        # on contextualise les réponses ws aux objets Odoo
        map_responses = {
            30204: "La 2eme ligne d'adresse du client partenaire "
            "est vide ou invalide",
            30221: "Le telephone du client ne doit comporter que des "
            "chiffres ou le symbole +: convertissez tous vos N° de "
            "telephone au format standard a partir du menu suivant:\n"
            "Configuration > Technique > Telephonie > Reformate "
            "les numeros de telephone ",
            30100: "La seconde ligne d'adresse de l'expéditeur est "
            "vide ou invalide.",
        }

        def format_one_exception(message, map_responses):
            param_message = {
                "ws_exception": "%s\n" % message["message"],
                "resolution": "",
            }
            if message and message.get("id") in map_responses.keys():
                param_message["resolution"] = _(
                    "Résolution\n-------------\n%s" % map_responses[message["id"]]
                )
            return _(
                "Réponse de Laposte:\n"
                "%(ws_exception)s\n%(resolution)s" % param_message
            )

        parts = []
        for messages in exception.args:
            for message in messages:
                parts.append(format_one_exception(message, map_responses))

        ret_mess = _(
            "Incident\n-----------\n%s\n"
            "Données transmises:\n"
            "-----------------------------\n%s"
        ) % ("\n".join(parts), request)
        return ret_mess

    def _laposte_fr_get_tracking_link(self):
        return (
            "https://www.colissimo.fr/"
            "portail_colissimo/suivreResultat.do?"
            "parcelnumber=%s" % self.parcel_tracking
        )

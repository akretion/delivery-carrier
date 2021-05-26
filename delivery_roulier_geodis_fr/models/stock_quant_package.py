#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          David BEAL <david.beal@akretion.com>
#          EBII MonsieurB <monsieurb@saaslys.com>
#          Sébastien BEAU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    geodis_cab = fields.Char(help="Barcode of the label")
    geodis_tracking_url = fields.Char(help="Public url for parcel tracking")

    def _geodis_generate_labels(self, picking):
        packages = self
        response = packages._call_roulier_api(picking)
        packages._handle_tracking(picking, response)
        packages._handle_attachments(picking, response)

    def _geodis_get_parcels(self, picking):
        return [pack._get_parcel(picking) for pack in self]

    def _geodis_before_call(self, picking, request):
        # TODO _get_options is called fo each package by the result
        # is the same. Should be store after first call
        picking._gen_shipping_id()  # explicit generation
        account = picking._get_account(self)
        service = account.get_data()
        request["service"]["customerId"] = service["customerId"]
        request["service"]["agencyId"] = service["agencyId"]
        request["service"]["hubId"] = service["hubId"]
        request["service"]["labelFormat"] = service["labelFormat"]
        request["service"]["shippingId"] = picking.geodis_shippingid
        request["service"]["is_test"] = service["isTest"]
        return request

    def _geodis_handle_tracking(self, picking, response):
        i = 0
        for rec in self:
            rec.write(
                {
                    "geodis_cab": response["parcels"][i]["number"],
                    "parcel_tracking": picking.geodis_shippingid,
                }
            )
            i += 1

    def _geodis_should_include_customs(self, picking):
        """Customs documents not implemented."""
        return False

    def _geodis_carrier_error_handling(self, payload, exception):
        pay = payload
        pay["auth"]["password"] = "****"
        return self._roulier_carrier_error_handling(payload, exception)

    def _geodis_get_tracking_link(self):
        return self.geodis_tracking_url

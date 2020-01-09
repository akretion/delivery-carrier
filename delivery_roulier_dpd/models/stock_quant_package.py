# coding: utf-8
#  @author Raphael Reverdy <raphael.reverdy@akretion.com>
#          EBII MonsieurB <monsieurb@saaslys.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models
import logging

_logger = logging.getLogger(__name__)


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    def _dpd_before_call(self, picking, request):
        # deprecated
        account = picking._get_account(self)
        service = account.get_data()
        request['service']['customerCountry'] = service['customerCountry']
        request['service']['customerId'] = service['customerId']
        request['service']['agencyId'] = service['agencyId']
        request['service']['labelFormat'] = service.get('labelFormat', 'ZPL')
        request['service']['product'] = picking.carrier_code
        request['service']['reference1'] = (
            picking.sale_id.name or picking.origin)

        if picking.carrier_code == "DPD_Relais":
            # deprecated
            request['service']['dropOffLocation'] = \
                self._dpd_dropoff_site(picking)
            request['service']['notifications'] = 'No'
        return request

    def _dpd_fr_before_call(self, picking, request):
        req = self._dpd_before_call(picking, request)
        account = picking._get_account(self)
        service = account.get_data()

        req['service'].update({
            "customerAddressId": service["customerAddressId"],
            "senderId": service["senderId"],
            "senderAddressId": service["senderAddressId"],
            "senderZipCode": service["senderZipCode"],
        })

        if picking.carrier_code == "DPD RELAIS":
            # deprecated
            req['service']['parcelShopId'] = \
                self._dpd_fr_parcelshopid(picking)

        return req


    @api.multi
    def _dpd_dropoff_site(self, picking):
        # deprecated
        return ''  # like P22895 TODO implement this

    @api.multi
    def _dpd_fr_parcelshopid(self, picking):
        # dropoff site = pacelshopid
        # = pickup point = point relais
        return ''  # like P22895 TODO implement this

    def _dpd_should_include_customs(self, picking):
        """DPD does not return customs documents"""
        return False

    def _dpd_fr_should_include_customs(self, picking):
        """DPD does not return customs documents"""
        return False

    def _dpd_carrier_error_handling(self, payload, exception):
        # deprecated
        return self._dpd_carrier_error_handling(payload, exception)

    def _dpd_fr_carrier_error_handling(self, payload, exception):
        if self._uid > 1:
            # rm pwd from dict and xml
            payload['auth']['password'] = '****'
        return self._roulier_carrier_error_handling(payload, exception)

    def _dpd_get_tracking_link(self):
        # deprecated
        return (
            "http://www.dpd.fr/home/shipping/searchdest.php?"
            "exa=%s" % self.parcel_tracking)

    def _dpd_fr_get_tracking_link(self):
        return (
            "http://www.dpd.fr/traces_%s"
            % self.parcel_tracking)

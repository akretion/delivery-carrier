# coding: utf-8
#  @author Raphael Reverdy @ Akretion <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta
from functools import wraps
import logging

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)
try:
    from roulier import roulier
    from roulier.exception import InvalidApiInput
except ImportError:
    _logger.debug('Cannot `import roulier`.')

# if you want to integrate a new carrier with Roulier Library
# start from roulier_template.py and read the doc of
# implemented_by_carrier decorator


def implemented_by_carrier(func):
    """Decorator: call _carrier_prefixed method instead.

    Usage:
        @implemented_by_carrier
        def _do_something()
        def _laposte_do_something()
        def _gls_do_something()

    At runtime, picking._do_something() will try to call
    the carrier spectific method or fallback to generic _do_something

    """
    @wraps(func)
    def wrapper(cls, *args, **kwargs):
        fun_name = func.__name__
        fun = '_%s%s' % (cls.carrier_type, fun_name)
        if not hasattr(cls, fun):
            fun = '_roulier%s' % (fun_name)
            # return func(cls, *args, **kwargs)
        return getattr(cls, fun)(*args, **kwargs)
    return wrapper


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    # API
    @implemented_by_carrier
    def _before_call(self, picking_id, request):
        pass

    @implemented_by_carrier
    def _after_call(self, picking_id, response):
        pass

    @implemented_by_carrier
    def _get_sender(self, picking_id):
        pass

    @implemented_by_carrier
    def _get_receiver(self, picking_id):
        pass

    @implemented_by_carrier
    def _get_shipping_date(self, picking_id):
        pass

    @implemented_by_carrier
    def _get_options(self, picking_id):
        pass

    @implemented_by_carrier
    def _get_customs(self, picking_id):
        pass

    @implemented_by_carrier
    def _should_include_customs(self, picking_id):
        pass

    @implemented_by_carrier
    def _get_auth(self, account):
        pass

    @implemented_by_carrier
    def _get_service(self, picking_id):
        pass

    @implemented_by_carrier
    def _get_parcel(self, picking_id):
        pass

    @implemented_by_carrier
    def _convert_address(self, partner):
        pass

    @implemented_by_carrier
    def _error_handling(self, payload, response):
        pass
    # end of API

    # Core functions

    @api.multi
    def _generate_labels(self, picking_id):
        ret = []
        for package in self:
            labels = package._call_roulier_api(picking_id)

            for label in labels:
                data = {
                    'name': label['name'],
                    'res_id': picking_id.id,
                    'res_model': 'stock.picking',
                    'package_id': package.id,
                }
                if label.get('url'):
                    data['url'] = label['url']
                    data['type'] = 'url'
                elif label.get('data'):
                    data['datas'] = label['data'].encode('base64')
                    data['type'] = 'binary'

                ret.append(self.env['shipping.label'].create(data))

        return ret

    def _call_roulier_api(self, picking_id):
        """Create a label for a given package_id (self)."""
        # There is low chance you need to override it.
        # Don't forget to implement _a-carrier_before_call
        # and _a-carrier_after_call
        self.ensure_one()

        self.carrier_type = picking_id.carrier_type  # on memory value !

        roulier_instance = roulier.get(picking_id.carrier_type)
        payload = roulier_instance.api()

        sender = self._get_sender(picking_id)
        receiver = self._get_receiver(picking_id)

        payload['auth'] = self._get_auth(picking_id)

        payload['from_address'] = self._convert_address(sender)
        payload['to_address'] = self._convert_address(receiver)

        if self._should_include_customs(picking_id):
            payload['customs'] = self._get_customs(picking_id)

        payload['service'] = self._get_service(picking_id)
        payload['parcel'] = self._get_parcel(picking_id)

        # sorte d'interceptor ici pour que chacun
        # puisse ajouter ses merdes à payload
        payload = self._before_call(picking_id, payload)
        # vrai appel a l'api
        try:
            ret = roulier_instance.get_label(payload)
        except InvalidApiInput as e:
            raise UserError(self._error_handling(payload, e.message))
        except Exception as e:
            raise UserError(e.message)

        # minimum error handling
        if ret.get('status', '') == 'error':
            raise UserError(self._error_handling(payload, ret))
        # give result to someone else
        return self._after_call(picking_id, ret)

    # helpers
    @api.model
    def _roulier_convert_address(self, partner):
        """Convert a partner to an address for roulier.

        params:
            partner: a res.partner
        return:
            dict
        """
        address = {}
        extract_fields = [
            'company', 'name', 'zip', 'city', 'phone', 'mobile',
            'email', 'street2']
        for elm in extract_fields:
            if elm in partner:
                # because a value can't be None in odoo's ORM
                # you don't want to mix (bool) False and None
                if partner._fields[elm].type != fields.Boolean.type:
                    if partner[elm]:
                        address[elm] = partner[elm]
                    # else:
                    # it's a None: nothing to do
                else:  # it's a boolean: keep the value
                    address[elm] = partner[elm]
        if not address.get('company', False) and partner.parent_id.is_company:
            address['company'] = partner.parent_id.name
        # Roulier needs street1 not street
        address['street1'] = partner.street
        # Codet ISO 3166-1-alpha-2 (2 letters code)
        address['country'] = partner.country_id.code
        return address

    # default implementations

    # if you want to implement your carrier behavior, don't override it,
    # but define your own method instead with your carrier prefix.
    # see documentation for more details about it
    def _roulier_get_auth(self, picking_id):
        """Login/password of the carrier account.

        Returns:
            a dict with login and password keys
        """
        auth = {
            'login': '',
            'password': '',
        }
        return auth

    def _roulier_get_service(self, picking_id):
        shipping_date = self._get_shipping_date(picking_id)

        service = {
            'product': picking_id.carrier_code,
            'shippingDate': shipping_date,
        }
        return service

    def _roulier_get_parcel(self, picking_id):
        weight = self.get_weight()
        parcel = {
            'weight': weight,
        }
        return parcel

    def _roulier_get_sender(self, picking_id):
        """Sender of the picking (for the label).

        Return:
            (res.partner)
        """
        return picking_id.company_id.partner_id

    def _roulier_get_receiver(self, picking_id):
        """The guy who the shippment is for.

        At home or at a distribution point, it's always
        the same receiver address.

        Return:
            (res.partner)
        """
        return picking_id.partner_id

    def _roulier_get_shipping_date(self, package_id):
        tomorrow = datetime.now() + timedelta(1)
        return tomorrow.strftime('%Y-%m-%d')

    def _roulier_get_options(self, picking_id):
        return {}

    def _roulier_get_customs(self, picking_id):
        return {}

    def _roulier_should_include_customs(self, picking_id):
        sender = self._get_sender(picking_id)
        receiver = self._get_receiver(picking_id)
        return sender.country_id.code == receiver.country_id.code

    @api.model
    def _roulier_error_handling(self, payload, response):
        return _(u'Sent data:\n%s\n\nException raised:\n%s\n' % (
            payload, self._error_handling(payload, response)))

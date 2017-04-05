# coding: utf-8
#  @author Raphael Reverdy @ Akretion <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from functools import wraps
import logging
import base64

from openerp import models, api, fields
from openerp.tools.translate import _
from openerp.exceptions import UserError

_logger = logging.getLogger(__name__)
try:
    from roulier import roulier
    from roulier.exception import (
        InvalidApiInput,
        CarrierError
    )
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

    carrier_id = fields.Many2one("delivery.carrier", string="Carrier")

    # helper : move it to base ?
    @api.multi
    def get_operations(self):
        """Get operations of the package.

        Usefull for having products and quantities
        """
        self.ensure_one()
        return self.env['stock.pack.operation'].search([
            ('result_package_id', '=', self.id),
            ('product_id', '!=', False),
        ])

    # API
    # Each method in this class have at least picking arg to directly
    # deal with stock.picking if required by your carrier use case
    @implemented_by_carrier
    def _before_call(self, picking, payload):
        pass

    @implemented_by_carrier
    def _after_call(self, picking, response):
        pass

    @implemented_by_carrier
    def _get_cash_on_delivery(self, picking):
        pass

    @implemented_by_carrier
    def _get_customs(self, picking):
        pass

    @implemented_by_carrier
    def _should_include_customs(self, picking):
        pass

    @implemented_by_carrier
    def _get_parcel(self, picking):
        pass

    @implemented_by_carrier
    def _carrier_error_handling(self, payload, response):
        pass

    @implemented_by_carrier
    def _invalid_api_input_handling(self, payload, response):
        pass

    @implemented_by_carrier
    def _prepare_label(self, label, picking):
        pass

    @implemented_by_carrier
    def _handle_attachments(self, label, response):
        pass

    @implemented_by_carrier
    def _handle_tracking(self, label, response):
        pass

    @implemented_by_carrier
    def _get_tracking_link(self):
        pass
    # end of API

    # Core functions

    @api.multi
    def _generate_labels(self, picking):
        ret = []
        for package in self:
            response = package._call_roulier_api(picking)
            package._handle_tracking(picking, response)
            attach = package._handle_attachments(picking, response)
            ret.append(attach.get('label'))
        return ret

    def _call_roulier_api(self, picking):
        """Create a label for a given package_id (self)."""
        # There is low chance you need to override it.
        # Don't forget to implement _a-carrier_before_call
        # and _a-carrier_after_call
        self.ensure_one()

        self.carrier_id = picking.carrier_id
        self.carrier_type = picking.carrier_type  # on memory value !
        roulier_instance = roulier.get(picking.carrier_type)
        payload = roulier_instance.api()

        sender = picking._get_sender(self)
        receiver = picking._get_receiver(self)

        payload['auth'] = picking._get_auth(self)

        payload['from_address'] = picking._convert_address(sender)
        payload['to_address'] = picking._convert_address(receiver)
        if self._should_include_customs(picking):
            payload['customs'] = self._get_customs(picking)

        payload['service'] = picking._get_service(self)
        payload['parcel'] = self._get_parcel(picking)

        # hook to override request / payload
        payload = self._before_call(picking, payload)
        try:
            # api call
            ret = roulier_instance.get_label(payload)
        except InvalidApiInput as e:
            raise UserError(self._invalid_api_input_handling(payload, e))
        except CarrierError as e:
            raise UserError(self._carrier_error_handling(payload, e))

        # give result to someone else
        return self._after_call(picking, ret)

    # default implementations

    def _roulier_handle_attachments(self, picking, response):
        main_label = self._roulier_prepare_label(picking, response)
        label = self.env['shipping.label'].create(main_label)

        attachments = self._roulier_prepare_attachments(picking, response)
        return {
            'label': label,
            'attachments': [
                self.env['ir.attachment'].create(attachment)
                for attachment in attachments
            ]
        }

    def _roulier_handle_tracking(self, picking, response):
        tracking = response.get('tracking')
        if tracking:
            number = tracking.get('number')
            if number:
                self.parcel_tracking = number

    @api.model
    def _roulier_prepare_label(self, picking, response):
        label = response.get('label')
        return {
            'res_id': picking.id,
            'res_model': 'stock.picking',
            'package_id': self.id,
            'name': "%s %s" % (self.name, label['name']),
            'datas': base64.b64encode(label['data']),
            'type': 'binary',
            'datas_fname': "%s-%s.%s" % (
                self.name, label['name'], label['type']),
        }

    def _roulier_prepare_attachments(self, picking, response):
        attachments = response.get('annexes')
        return [{
            'res_id': picking.id,
            'res_model': 'stock.picking',
            'name': "%s %s" % (self.name, attachment['name']),
            'datas': base64.b64encode(attachment['data']),
            'type': 'binary',
            'datas_fname': "%s-%s.%s" % (
                self.name, attachment['name'], attachment['type']),
        } for attachment in attachments]

    def _roulier_get_parcel(self, picking):
        weight = self.weight
        parcel = {
            'weight': weight,
        }
        return parcel

    def _roulier_get_cash_on_delivery(self, picking):
        """ called by 'cod' option
        """
        # TODO improve to take account Sale if picking created from sale
        amount = 0
        for oper in self.get_operations():
            amount += oper.product_id.list_price * oper.product_qty
        return amount

    def _roulier_get_customs(self, picking):
        """Format customs infos for each product in the package.

        The decision whether to include these infos or not is
        taken in _should_include_customs()

        Returns:
            dict.'articles' : list with qty, weight, hs_code
            int category: gift 1, sample 2, commercial 3, ...
        """
        def ensure_hs_codes_available():
            try:
                self.env['product.template'].get_hs_code_recursively
            except AttributeError:
                raise UserError(_("Missing module 'intrastat' for customs"))

        ensure_hs_codes_available()
        articles = []
        for operation in self.get_operations():
            article = {}
            articles.append(article)
            product = operation.product_id
            # stands for harmonized_system
            hs = product.product_tmpl_id.get_hs_code_recursively()

            article['quantity'] = '%.f' % operation.product_qty
            article['weight'] = (
                operation.get_weight() / operation.product_qty)
            article['originCountry'] = product.origin_country_id.code
            article['description'] = hs.description
            article['hs'] = hs.hs_code
            article['value'] = product.list_price  # unit price is expected

        category = picking.customs_category
        return {
            "articles": articles,
            "category": category,
        }

    def _roulier_before_call(self, picking, payload):
        return payload

    def _roulier_after_call(self, picking, response):
        return response

    def _roulier_should_include_customs(self, picking):
        sender = picking._get_sender(self)
        receiver = picking._get_receiver(self)
        return sender.country_id.code != receiver.country_id.code

    @api.model
    def _roulier_carrier_error_handling(self, payload, exception):
        return _(u'Sent data:\n%s\n\nException raised:\n%s\n' % (
            payload, exception.message))

    def _roulier_invalid_api_input_handling(self, payload, exception):
        return _(u'Bad input: %s\n', exception.message)

    def _roulier_open_tracking_url(self):
        _logger.warning("not implemented")
        pass

    def _roulier_get_tracking_link(self):
        _logger.warning("not implemented")
        pass

    @api.multi
    def open_website_url(self):
        self.ensure_one()
        self.carrier_type = self.carrier_id.carrier_type
        url = self._get_tracking_link()
        client_action = {
            'type': 'ir.actions.act_url',
            'name': "Shipment Tracking Page",
            'target': 'new',
            'url': url,
        }
        return client_action
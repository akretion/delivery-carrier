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


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # base_delivery_carrier_label API implementataion

    # @api.multi
    # def generate_default_label(self, package_ids=None):
    # useless method

    @api.multi
    def _is_roulier(self):
        self.ensure_one()
        return self.carrier_type in roulier.get_carriers()

    @api.multi
    def generate_labels(self, package_ids=None):
        """See base_delivery_carrier_label/stock.py."""
        # entry point
        self.ensure_one()
        if self._is_roulier():
            return self._roulier_generate_labels()
        _super = super(StockPicking, self)
        return _super.generate_labels(package_ids=package_ids)

    @api.multi
    def generate_shipping_labels(self, package_ids=None):
        """See base_delivery_carrier_label/stock.py."""
        self.ensure_one()

        if self._is_roulier():
            raise UserError(_("Don't call me directly"))
        _super = super(StockPicking, self)
        return _super.generate_shipping_labels(package_ids=package_ids)

    @api.multi
    def _roulier_generate_labels(self):
        """Create as many labels as package_ids or in self."""
        self.ensure_one()
        packages = self._get_packages_from_picking()
        if not packages:
            # It's not our responsibility to create the packages
            raise UserError(_('No package found for this picking'))
        return packages._generate_labels(self)

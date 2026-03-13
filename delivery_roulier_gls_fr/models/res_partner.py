# @author Olivier Nibart <olivier.nibart@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    dropoff_site = fields.Char(
        help="Carrier-specific drop-off site identifier. "
        "Used when this partner location serves as a pickup point.",
    )

    def apply_recipient_contact_to_dropoff_site(self, recipient_partner_id):
        """Overlay recipient's contact details onto a carrier drop-off site address.

        A drop-off site must be kept as the shipping address for two reasons:
        - It's the address the carrier will use  for physical routing.
        - Odoo derives the fiscal position from the shipping address country,
          so preserving it ensures correct tax handling for such edge cases.
          (it may be in a different country than the customer, e.g. cross-border
          shoppers using a foreign relay)
        The carrier however requires the actual recipient's name, email and
        phone to identify the parcel and trigger delivery notifications — hence
        this overlay: postal address stays, contact identity is replaced.
        """
        self.ensure_one()
        self.name = recipient_partner_id.name
        self.email = recipient_partner_id.email
        self.phone = recipient_partner_id.phone
        self.mobile = recipient_partner_id.mobile

# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import date, timedelta

from markupsafe import Markup, escape

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import format_list

from roulier import roulier
from roulier.exception import CarrierError, InvalidApiInput

from ..utils import split_partner_address

carrier_actions = roulier.get_carriers_action_available()
handled_carriers = [
    carrier
    for carrier, actions in carrier_actions.items()
    if set(("get_metadata", "get_label")) <= set(actions)
]
metadata = {
    carrier: roulier.get(carrier, "get_metadata", None) for carrier in handled_carriers
}


class Helper(models.AbstractModel):
    _name = "helper"

    def __getattr__(self, name):
        # Hack for abstract helper in 18.0, this allows to use related as a bonus
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            if name == "id":
                return self._ids[0]
            raise


class RoulierHelper(Helper):
    _name = "roulier.helper"
    _description = "Roulier Helper"

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Carrier",
        required=True,
    )

    type = fields.Selection(
        related="carrier_id.delivery_type",
    )

    @property
    def metadata(self):
        """Get the metadata for the current carrier type."""
        return self.carrier_id.metadata

    @property
    def properties(self):
        """Get the properties for the current carrier type."""
        return self.carrier_id.roulier_properties

    def _get_account(self, packages=None):
        """Get the account information for the Roulier API."""
        if packages:
            # If we have specified packages and they come from a picking
            # Prefer calling the _get_carrier_account method
            for pkg in packages:
                if pkg.picking_id:
                    return pkg.picking_id._get_carrier_account()

        return self.carrier_id.carrier_account_id

    # Conversion methods
    def _get_auth(self, packages=None):
        """Get the authentication information"""
        account = self._get_account(packages)
        return {
            "login": account.account,
            "password": account.password,
            "isTest": self.properties.get("test_mode", False),
        }

    def _get_shipping_date(self, packages=None):
        """Get the shipping date"""

        tomorrow = date.today() + timedelta(1)
        return tomorrow

    def _get_service(self, packages=None):
        """Get the service information"""
        # TODO: find a way to describe the service from the roulier API
        # and specify it in the source object

        vals = {
            "product": self.carrier_id.code,
        }

        shipping_date = self._get_shipping_date(packages)
        if shipping_date:
            vals["shippingDate"] = shipping_date

        if self.properties.get("output_format"):
            vals["labelFormat"] = self.properties["output_format"]

        for option in self.metadata.get("options", []):
            key = option["name"]
            if key != "product" and self.properties.get(key.lower()):
                vals[key] = self.properties[key.lower()]

        return vals

    def _get_parcel(self, package):
        """Get the parcel from the package."""
        return {
            "weight": package.weight,
            "reference": package.name,
        }

    def _get_address(self, partner):
        """Get a roulier address from a partner record."""

        return {
            "company": partner.company_name or partner.is_company and partner.name,
            "name": partner.name,
            "city": partner.city,
            "country": partner.country_id.code,
            "zip": partner.zip,
            "phone": partner.mobile or partner.phone,
            **split_partner_address(
                partner,
                max_length=self.metadata.get("address_format", {}).get("max_length"),
                address_count=self.metadata.get("address_format", {}).get("count"),
            ),
        }

    def _get_sender_address(self, sender):
        """Sender specific conversion."""
        return self._get_address(sender)

    def _get_receiver_address(self, receiver):
        """Receiver specific conversion."""
        return self._get_address(receiver)

    def _get_parcels(self, packages):
        """Get the parcels from the packages."""
        return [self._get_parcel(package) for package in packages]

    # Roulier API
    def _call_api(self, method, payload):
        try:
            return roulier.get(self.type, method, payload)
        except CarrierError as e:
            raise UserError(
                _(
                    "Roulier API carrier error: %(error)s\n%(payload)s",
                    error=e,
                    payload=payload,
                )
            ) from e
        except InvalidApiInput as e:
            raise UserError(
                _(
                    "Roulier API input error: %(error)s\n%(payload)s",
                    error=e,
                    payload=payload,
                )
            ) from e

    def _get_label(self, payload):
        return self._call_api("get_label", payload)

    def get_tracking_link(self, tracking_number):
        if "get_tracking_link" in carrier_actions.get(self.type, []):
            return self._call_api("get_tracking_link", tracking_number)

    # Helper methods
    def send_packages(
        self,
        packages,
        sender=None,
        receiver=None,
    ):
        """Send packages to Roulier Service API and return the response."""

        payload = {
            "auth": self._get_auth(packages),
            "service": self._get_service(packages),
            "parcels": self._get_parcels(packages),
            "from_address": self._get_sender_address(sender),
            "to_address": self._get_receiver_address(receiver),
        }

        return self._get_label(payload)

    def extract_parcel_prices(self, response):
        parcels = response.get("parcels", [])
        return sum(
            [parcel["price"] for parcel in parcels if parcel and parcel.get("price")]
        )

    def extract_parcel_tracking(self, response):
        parcels = response.get("parcels", [])
        # Yes, this is the odoo way:
        return "+".join(
            [
                parcel["tracking"]["number"]
                for parcel in parcels
                if parcel and parcel.get("tracking", {}).get("number")
            ]
        )

    def _find_matching_package(self, parcel, packages):
        """Find the delivery package that matches the parcel reference."""
        for package in packages:
            if package.name == parcel.get("reference"):
                return package

    def _get_quant_package_from_package(self, package):
        """Get the quant package from the package."""
        if package.picking_id:
            return package.picking_id.move_line_ids.result_package_id.filtered(
                lambda quant_package: quant_package.name == package.name
            )

    def _get_shipping_label_values(self, source, label):
        self.ensure_one()
        return {
            "name": label.get("name", "label"),
            "res_id": self.id,
            "res_model": source._name,
            "datas": label.get("data"),
            "file_type": label.get("type"),
        }

    def _process_labels(self, source, results, packages):
        parcels = results.get("parcels", [])
        shipping_labels = self.env["shipping.label"]
        for parcel in parcels:
            if not parcel.get("label") or not parcel["label"].get("data"):
                continue
            label = parcel["label"]

            shipping_label = self.env["shipping.label"].create(
                self._get_shipping_label_values(source, label)
            )

            # Attach the label to the corresponding package if it exists
            package = self._find_matching_package(parcel, packages)
            quant_package = self._get_quant_package_from_package(package)
            tracking_number = parcel.get("tracking", {}).get("number")
            if shipping_label.name == "label":
                shipping_label.name = tracking_number
            if quant_package:
                quant_package.write(
                    {
                        "carrier_id": self.carrier_id.id,
                        "parcel_tracking": tracking_number,
                    }
                )
                shipping_label.write(
                    {
                        "name": f"{quant_package.name} - {shipping_label.name}",
                        "package_id": quant_package.id,
                    }
                )

            shipping_labels |= shipping_label

        return shipping_labels

    def _get_attachments(self, results):
        """Get the non-label attachments from the results."""
        annexes = results.get("annexes", [])
        return [
            (annex["name"], annex["data"]) for annex in annexes if annex.get("data")
        ]

    def _get_message(self, results):
        """Get the message to attach to the source object."""
        return Markup(
            (
                "<p>"
                "{type}<br/>"
                "<b>{tracking_label}:</b> {tracking_numbers}<br/>"
                "<b>{packages_label}:</b> {packages}"
                "</p>"
            ).format(
                type=escape(_("Shipment created with %(type)s") % dict(type=self.type)),
                tracking_label=escape(_("Tracking Numbers")),
                tracking_numbers=escape(self.extract_parcel_tracking(results)),
                packages_label=escape(_("Packages")),
                packages=escape(
                    format_list(
                        self.env,
                        [
                            parcel["reference"]
                            for parcel in results.get("parcels", [])
                            if parcel.get("reference")
                        ],
                    )
                ),
            )
        )

    def attach_results(self, source, results, packages):
        """Attach the results to the source object."""
        # Attach the labels
        labels = self._process_labels(source, results, packages)

        source.message_post(
            body=self._get_message(results),
            attachments=self._get_attachments(results),
            attachment_ids=labels.attachment_id.ids,
        )

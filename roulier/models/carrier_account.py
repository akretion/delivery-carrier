# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models

from .roulier_helper import handled_carriers, metadata


class CarrierAccount(models.Model):
    _inherit = "carrier.account"

    is_roulier = fields.Boolean(
        compute="_compute_is_roulier",
        store=True,
    )
    delivery_carrier_ids = fields.One2many(
        comodel_name="delivery.carrier",
        inverse_name="carrier_account_id",
        string="Delivery Carriers",
    )
    roulier_properties_definition = fields.PropertiesDefinition(
        compute="_compute_roulier_properties_definition"
    )

    @api.depends("delivery_type")
    def _compute_is_roulier(self):
        for record in self:
            record.is_roulier = record.delivery_type in handled_carriers

    def _roulier_option_to_property(self, option):
        """Convert Roulier option to property"""
        prop = {"name": option["name"].lower(), "string": option["label"]}

        prop["type"] = option.get("type", "char")

        prop["type"] = {
            "string": "char",
            "select": "selection",
        }.get(prop["type"], prop["type"])

        if prop.get("default") is not None:
            prop["default"] = option["default"]

        if prop["type"] == "selection":
            values = option.get("values", {})
            if values and not isinstance(values, dict):
                values = {value: value for value in values}

            prop["selection"] = [(value, label) for value, label in values.items()]

        return prop

    def _roulier_properties_from_metadata(self, metadata):
        """Convert Roulier metadata to properties"""
        return [
            {
                "name": "default_packaging_id",
                "string": "Default Packaging",
                "type": "many2one",
                "comodel": "stock.package.type",
            },
        ] + [
            self._roulier_option_to_property(option)
            for option in metadata.get("options", [])
            if option["name"] not in ["product"]
        ]

    @api.depends("delivery_type")
    def _compute_roulier_properties_definition(self):
        for record in self:
            if record.is_roulier:
                record.roulier_properties_definition = (
                    record._roulier_properties_from_metadata(
                        metadata.get(record.delivery_type, {})
                    )
                )
            else:
                record.roulier_properties_definition = []

    def _get_delivery_product(self, code, name):
        """Get the product for the delivery carrier"""
        product_category_deliveries = self.env.ref(
            "delivery.product_category_deliveries"
        )
        delivery_product = self.env["product.product"].search(
            [
                ("default_code", "=", code),
                ("categ_id", "=", product_category_deliveries.id),
            ],
            limit=1,
        )
        if not delivery_product:
            delivery_product = self.env["product.product"].create(
                {
                    "name": f"{self.name} - {name}",
                    "default_code": code,
                    "type": "service",
                    "categ_id": product_category_deliveries.id,
                    "sale_ok": False,
                    "purchase_ok": False,
                    "list_price": True,
                    "invoice_policy": "order",
                }
            )
        return delivery_product

    def _prepare_roulier_product_vals(self, code, name):
        """Prepare values for creating a new product in Roulier"""
        return {
            "name": f"{self.name} - {name}",
            "delivery_type": self.delivery_type,
            "code": code,
            "carrier_account_id": self.id,
            "product_id": self._get_delivery_product(code, name).id,
        }

    def sync_roulier_carriers(self):
        """Sync Delivery Carriers with Provider product property"""
        for account in self:
            data = metadata.get(account.delivery_type, {})
            if account.delivery_type in handled_carriers:
                carriers = account.delivery_carrier_ids
                products = []
                for option in data.get("options", []):
                    if option["name"] == "product":
                        products = option.get("values", {})
                        if not isinstance(products, dict):
                            products = {product: product for product in products}
                        break

                for code, name in products.items():
                    carrier = carriers.filtered(lambda c, code=code: c.code == code)

                    if not carrier:
                        self.env["delivery.carrier"].create(
                            account._prepare_roulier_product_vals(code, name)
                        )

    @api.model_create_multi
    def create(self, vals_list):
        accounts = super().create(vals_list)
        accounts.sync_roulier_carriers()
        return accounts

    def write(self, vals):
        res = super().write(vals)
        if "delivery_type" in vals:
            self.sync_roulier_carriers()
        return res

# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.tests import RecordCapturer

from .common import RoulierCommonCase


class RoulierMetadataCase(RoulierCommonCase):
    def test_delivery_carrier_selection_fields(self):
        entries = self.env["delivery.carrier"]._fields["delivery_type"].selection
        self.assertIn(("colissimo_fr", "Colissimo France"), entries)
        self.assertIn(("dpd_fr", "DPD France"), entries)
        self.assertIn(("mondialrelay_fr", "Mondial Relay France"), entries)

    def test_delivery_carrier_options(self):
        account = self.env["carrier.account"].create(
            {
                "name": "Colissimo",
                "delivery_type": "colissimo_fr",
                "account": "colissimo_account",
                "password": "colissimo_password",
            }
        )
        definitions = {
            def_["name"]: def_ for def_ in account.roulier_carrier_properties_definition
        }
        self.assertIn("labelformat", definitions)
        self.assertIn("customerid", definitions)

        self.assertEqual(definitions["labelformat"]["string"], "Label Format")
        self.assertEqual(definitions["labelformat"]["type"], "selection")
        self.assertIn(["PDF", "PDF"], definitions["labelformat"]["selection"])
        self.assertIn(
            ["ZPL_10x15_203dpi", "ZPL_10x15_203dpi"],
            definitions["labelformat"]["selection"],
        )

        self.assertEqual(definitions["customerid"]["string"], "Customer ID")
        self.assertEqual(definitions["customerid"]["type"], "char")

    def test_delivery_carrier_generation(self):
        products = next(
            option
            for option in self._roulier_metadata["colissimo_fr"]["options"]
            if option["name"] == "product"
        )["values"]
        with RecordCapturer(self.env["delivery.carrier"], []) as captured:
            self.env["carrier.account"].create(
                {
                    "name": "Colissimo",
                    "delivery_type": "colissimo_fr",
                    "account": "colissimo_account",
                    "password": "colissimo_password",
                }
            )
            deliveries = captured.records
            self.assertEqual(len(deliveries), len(products))
            dom_delivery = deliveries.filtered(lambda d: d.code == "DOM")
            self.assertTrue(dom_delivery)
            self.assertEqual(
                dom_delivery.name, "Colissimo - Home delivery without signature"
            )
            self.assertEqual(dom_delivery.delivery_type, "colissimo_fr")

    def test_delivery_delivery_options(self):
        account = self.env["carrier.account"].create(
            {
                "name": "Colissimo",
                "delivery_type": "colissimo_fr",
                "account": "colissimo_account",
                "password": "colissimo_password",
            }
        )
        definitions = {
            def_["name"]: def_
            for def_ in account.delivery_carrier_ids[
                0
            ].roulier_delivery_properties_definition
        }
        self.assertIn("default_packaging_id", definitions)
        self.assertEqual(
            definitions["default_packaging_id"]["string"], "Default Packaging"
        )
        self.assertEqual(definitions["default_packaging_id"]["type"], "many2one")
        self.assertEqual(
            definitions["default_packaging_id"]["comodel"], "stock.package.type"
        )

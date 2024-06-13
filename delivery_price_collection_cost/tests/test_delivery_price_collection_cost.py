# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.tests import Form
from odoo.tests.common import SavepointCase


class TestDeliveryPriceCollectionCost(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_shipping_cost, cls.product_collection_cost = cls.env[
            "product.product"
        ].create(
            [
                {
                    "type": "service",
                    "name": "Shipping costs",
                    "list_price": 100,
                },
                {
                    "type": "service",
                    "name": "Collection costs",
                    "list_price": 45,
                    "description_sale": "Collection cost description",
                },
            ]
        )
        (
            cls.carrier_no_collection,
            cls.carrier_fixed_collection,
            cls.carrier_rule_collection,
        ) = cls.env["delivery.carrier"].create(
            [
                {
                    "name": "Carrier no collection",
                    "delivery_type": "fixed",
                    "product_id": cls.product_shipping_cost.id,
                },
                {
                    "name": "Carrier fixed collection",
                    "delivery_type": "fixed",
                    "product_id": cls.product_shipping_cost.id,
                    "collection_product_id": cls.product_collection_cost.id,
                },
                {
                    "name": "Carrier rule collection",
                    "delivery_type": "base_on_rule",
                    "product_id": cls.product_shipping_cost.id,
                    "collection_product_id": cls.product_collection_cost.id,
                    "price_rule_ids": [
                        (
                            0,
                            0,
                            {
                                "variable": "quantity",
                                "operator": "==",
                                "max_value": 1,
                                "list_base_price": 11.11,
                                "collection_price": 10.10,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "variable": "quantity",
                                "operator": "==",
                                "max_value": 2,
                                "list_base_price": 22.22,
                                "collection_price": 20.20,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "variable": "quantity",
                                "operator": ">",
                                "max_value": 2,
                                "list_base_price": 33.33,
                                "collection_price": 0,
                            },
                        ),
                    ],
                },
            ]
        )
        cls.product = cls.env.ref("product.product_delivery_01")
        cls.partner = cls.env.ref("base.res_partner_12")
        cls.sale = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    (0, 0, {"product_id": cls.product.id, "product_uom_qty": 1})
                ],
            }
        )

    def _add_delivery(self, carrier, sale=None):
        if sale is None:
            sale = self.sale
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {"default_order_id": sale.id, "default_carrier_id": carrier}
            )
        )
        delivery_wizard.save().button_confirm()

    def _get_delivery_lines(self, sale=None):
        if sale is None:
            sale = self.sale
        delivery_line = sale.order_line.filtered("is_delivery")
        collection_line = sale.order_line.filtered("is_delivery_collection")
        return delivery_line, collection_line

    def test_delivery_no_collection(self):
        """
        If no collection product is set, the flow should be unaffected
        only a single shipping product
        """
        self._add_delivery(self.carrier_no_collection)
        delivery_line, collection_line = self._get_delivery_lines()
        self.assertEqual(len(delivery_line), 1)
        self.assertEqual(delivery_line.product_id, self.product_shipping_cost)
        self.assertEqual(
            delivery_line.price_unit, self.product_shipping_cost.list_price
        )
        self.assertFalse(collection_line)

    def test_delivery_collection_fixed(self):
        """
        If a collection product is set,
        the SOL should have two lines. Fixed price
        """
        self._add_delivery(self.carrier_fixed_collection)
        delivery_line, collection_line = self._get_delivery_lines()
        self.assertEqual(len(delivery_line), 1)
        self.assertEqual(delivery_line.product_id, self.product_shipping_cost)
        self.assertEqual(
            delivery_line.price_unit, self.product_shipping_cost.list_price
        )
        self.assertEqual(len(collection_line), 1)
        self.assertEqual(collection_line.product_id, self.product_collection_cost)
        self.assertEqual(
            collection_line.price_unit, self.carrier_fixed_collection.collection_price
        )
        self.assertEqual(
            collection_line.name, self.product_collection_cost.description_sale
        )

    def test_delivery_collection_rule(self):
        """
        If a collection product is set,
        the SOL should have two lines.
        Price depends on the rule that's applied
        """
        self._add_delivery(self.carrier_rule_collection)
        delivery_line, collection_line = self._get_delivery_lines()
        self.assertEqual(len(delivery_line), 1)
        self.assertEqual(delivery_line.product_id, self.product_shipping_cost)
        self.assertEqual(delivery_line.price_unit, 11.11)
        self.assertEqual(len(collection_line), 1)
        self.assertEqual(collection_line.product_id, self.product_collection_cost)
        self.assertEqual(collection_line.price_unit, 10.10)
        self.assertEqual(
            collection_line.name, self.product_collection_cost.description_sale
        )
        # change the qty to apply another rule
        self.sale.order_line[0].product_uom_qty = 2
        self._add_delivery(self.carrier_rule_collection)
        delivery_line, collection_line = self._get_delivery_lines()
        self.assertEqual(len(delivery_line), 1)
        self.assertEqual(delivery_line.product_id, self.product_shipping_cost)
        self.assertEqual(delivery_line.price_unit, 22.22)
        self.assertEqual(len(collection_line), 1)
        self.assertEqual(collection_line.product_id, self.product_collection_cost)
        self.assertEqual(collection_line.price_unit, 20.20)
        self.assertEqual(
            collection_line.name, self.product_collection_cost.description_sale
        )
        # change the qty --> rule says collection price is 0 --> no collection line
        self.sale.order_line[0].product_uom_qty = 3
        self._add_delivery(self.carrier_rule_collection)
        delivery_line, collection_line = self._get_delivery_lines()
        self.assertEqual(len(delivery_line), 1)
        self.assertEqual(delivery_line.product_id, self.product_shipping_cost)
        self.assertEqual(delivery_line.price_unit, 33.33)
        self.assertFalse(collection_line)

    def test_delivery_lines_removal(self):
        self._add_delivery(self.carrier_fixed_collection)
        delivery_line, collection_line = self._get_delivery_lines()
        self.assertEqual(len(delivery_line), 1)
        self.assertEqual(len(collection_line), 1)
        self.sale._remove_delivery_line()
        delivery_line, collection_line = self._get_delivery_lines()
        self.assertFalse(delivery_line)
        self.assertFalse(collection_line)
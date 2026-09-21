# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import Form, common


class TestDeliveryDiscountedFreeOver(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.SaleOrder = self.env["sale.order"]
        self.SaleOrderLine = self.env["sale.order.line"]
        self.AccountAccount = self.env["account.account"]
        self.SaleConfigSetting = self.env["res.config.settings"]
        self.Product = self.env["product.product"]

        self.partner_18 = self.env["res.partner"].create({"name": "My Test Customer"})
        self.pricelist = self.env.ref("product.list0")
        self.product_4 = self.env["product.product"].create(
            {"name": "A product to deliver", "weight": 1.0}
        )
        self.product_uom_unit = self.env.ref("uom.product_uom_unit")
        self.product_delivery_normal = self.env["product.product"].create(
            {
                "name": "Normal Delivery Charges",
                "type": "service",
                "list_price": 10.0,
                "categ_id": self.env.ref("delivery.product_category_deliveries").id,
            }
        )
        self.normal_delivery = self.env["delivery.carrier"].create(
            {
                "product_id": self.product_delivery_normal.id,
                "name": "Normal Delivery Charges",
                "delivery_type": "fixed",
                "fixed_price": 100.0,
                "free_over": True,
                "amount": 500.0,
            }
        )
        self.partner_4 = self.env["res.partner"].create({"name": "Another Customer"})
        self.partner_address_13 = self.env["res.partner"].create(
            {
                "name": "Another Customer's Address",
                "parent_id": self.partner_4.id,
            }
        )
        self.product_uom_hour = self.env.ref("uom.product_uom_hour")
        self.account_data = self.env.ref("account.data_account_type_revenue")
        self.account_tag_operating = self.env.ref("account.account_tag_operating")
        self.product_2 = self.env["product.product"].create(
            {"name": "Zizizaproduct", "weight": 1.0}
        )
        self.product_category = self.env.ref("product.product_category_all")
        self.free_delivery = self.env.ref("delivery.free_delivery_carrier")
        # as the tests hereunder assume all the prices in USD, we must ensure
        # that the company actually uses USD
        # We do an invalidate_cache so the cache is aware of it too.
        self.env.cr.execute(
            "UPDATE res_company SET currency_id = %s WHERE id = %s",
            [self.env.ref("base.USD").id, self.env.company.id],
        )
        self.env.company.invalidate_cache()
        self.pricelist.currency_id = self.env.ref("base.USD").id

    def test_normal_free_over_behaviour_no_free_over(self):
        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner_18.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_4.id,
                            "product_uom_qty": 1,
                            "price_unit": 250.00,
                        }
                    )
                ],
            }
        )

        # Add of delivery cost in Sales order
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=so.id,
                default_carrier_id=self.normal_delivery.id,
            )
        )
        self.assertEqual(
            delivery_wizard.delivery_price,
            100.0,
        )
        delivery_wizard.save().button_confirm()

        line = so.order_line.filtered_domain(
            [("product_id", "=", self.normal_delivery.product_id.id)]
        )
        self.assertEqual(len(line), 1)
        self.assertEqual(line.price_unit, 100.0)
        self.assertEqual(line.product_uom_qty, 1)
        self.assertEqual(line.discount, 0)
        self.assertEqual(line.price_subtotal, 100.0)

    def test_normal_free_over_behaviour_free_over(self):
        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner_18.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_4.id,
                            "product_uom_qty": 1,
                            "price_unit": 750.00,
                        }
                    )
                ],
            }
        )

        # Add of delivery cost in Sales order
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=so.id,
                default_carrier_id=self.normal_delivery.id,
            )
        )
        self.assertEqual(
            delivery_wizard.delivery_price,
            0.0,
        )
        delivery_wizard.save().button_confirm()

        line = so.order_line.filtered_domain(
            [("product_id", "=", self.normal_delivery.product_id.id)]
        )
        self.assertEqual(len(line), 1)
        self.assertEqual(line.price_unit, 0.0)
        self.assertEqual(line.product_uom_qty, 1)
        self.assertEqual(line.discount, 0)
        self.assertEqual(line.price_subtotal, 0.0)

    def test_discounted_free_over_behaviour_no_free_over(self):
        self.env.company.free_over_as_discount = True
        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner_18.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_4.id,
                            "product_uom_qty": 1,
                            "price_unit": 250.00,
                        }
                    )
                ],
            }
        )

        # Add of delivery cost in Sales order
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=so.id,
                default_carrier_id=self.normal_delivery.id,
            )
        )
        self.assertEqual(
            delivery_wizard.delivery_price,
            100.0,
        )
        delivery_wizard.save().button_confirm()

        line = so.order_line.filtered_domain(
            [("product_id", "=", self.normal_delivery.product_id.id)]
        )
        self.assertEqual(len(line), 1)
        self.assertEqual(line.price_unit, 100.0)
        self.assertEqual(line.product_uom_qty, 1)
        self.assertEqual(line.discount, 0)
        self.assertEqual(line.price_subtotal, 100.0)

    def test_discounted_free_over_behaviour_free_over(self):
        self.env.company.free_over_as_discount = True
        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner_18.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_4.id,
                            "product_uom_qty": 1,
                            "price_unit": 750.00,
                        }
                    )
                ],
            }
        )

        # Add of delivery cost in Sales order
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=so.id,
                default_carrier_id=self.normal_delivery.id,
            )
        )
        self.assertEqual(
            delivery_wizard.delivery_price,
            0.0,
        )
        delivery_wizard.save().button_confirm()

        line = so.order_line.filtered_domain(
            [("product_id", "=", self.normal_delivery.product_id.id)]
        )
        self.assertEqual(len(line), 1)
        self.assertEqual(line.price_unit, 100.0)
        self.assertEqual(line.product_uom_qty, 1)
        self.assertEqual(line.discount, 100.0)
        self.assertEqual(line.price_subtotal, 0.0)

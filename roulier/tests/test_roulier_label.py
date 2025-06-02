# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo.tests import RecordCapturer
from .common import RoulierColissimoPatchedCase


class RoulierLabelCase(RoulierColissimoPatchedCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "is_storable": True,
                "weight": 3.14,
                "default_code": "TEST123",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "email": "test@example.com",
                "phone": "123456789",
                "street": "123 Test Street",
                "city": "Test City",
                "zip": "12345",
                "country_id": cls.env.ref("base.fr").id,
                "company_name": cls.env.company.name,
            }
        )
        cls.order = cls.env["sale.order"].create(
            {
                "carrier_id": cls.delivery.id,
                "partner_id": cls.partner.id,
                "order_line": [
                    (0, 0, {"product_id": cls.product.id, "product_uom_qty": 1})
                ],
            }
        )
        cls.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": cls.product.id,
                "location_id": cls.order.warehouse_id.lot_stock_id.id,
                "inventory_quantity": 1,
            }
        ).action_apply_inventory()

    def test_get_label_from_picking_without_pack(self):
        self.order.action_confirm()
        self.picking = self.order.picking_ids

        with (
            RecordCapturer(self.env["mail.message"], []) as captured_messages,
            RecordCapturer(self.env["shipping.label"], []) as captured_labels,
        ):
            self.picking.button_validate()

        self.assertTrue(self.picking.state == "done")
        self.assertEqual(len(captured_messages.records), 2)
        self.assertIn(
            "Shipment created with colissimo_fr "
            "Tracking Numbers: TRACKING_NUMBER "
            "Packages: Bulk Content",
            captured_messages.records.mapped("preview"),
        )
        self.assertEqual(len(captured_labels.records), 1)
        label = captured_labels.records[0]
        self.assertFalse(label.package_id)
        request = self._get_request(label.raw)
        self.assertEqual(request["contractNumber"], "colissimo_account")
        self.assertEqual(request["password"], "colissimo_password")
        self.assertEqual(request["letter"]["service"]["productCode"], "DOM")
        self.assertEqual(
            request["letter"]["service"]["depositDate"],
            (date.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
        )
        self.assertEqual(request["letter"]["parcel"]["weight"], 3.14)
        self.assertEqual(
            request["outputFormat"]["outputPrintingType"], "DPL_10x15_203dpi_UL"
        )
        self.assertEqual(
            request["letter"]["sender"]["address"]["companyName"],
            self.env.company.name,
        )
        self.assertEqual(
            request["letter"]["sender"]["address"]["line2"],
            "250 Executive Park Blvd, Suite",
        )
        self.assertEqual(request["letter"]["sender"]["address"]["line0"], "3400")
        self.assertEqual(
            request["letter"]["sender"]["address"]["city"], "San Francisco"
        )
        self.assertEqual(request["letter"]["sender"]["address"]["zipCode"], "94134")
        self.assertEqual(
            request["letter"]["addressee"]["address"]["lastName"], "Test Partner"
        )
        self.assertEqual(
            request["letter"]["addressee"]["address"]["line2"], "123 Test Street"
        )
        self.assertEqual(request["letter"]["addressee"]["address"]["city"], "Test City")
        self.assertEqual(request["letter"]["addressee"]["address"]["zipCode"], "12345")
        self.assertEqual(request["letter"]["addressee"]["address"]["countryCode"], "FR")
        self.assertEqual(
            request["letter"]["addressee"]["address"]["mobileNumber"], "123456789"
        )

    def test_get_label_from_picking_in_pack(self):
        self.order.action_confirm()
        self.picking = self.order.picking_ids

        package = self.picking._put_in_pack(self.picking.move_line_ids)

        with (
            RecordCapturer(self.env["mail.message"], []) as captured_messages,
            RecordCapturer(self.env["shipping.label"], []) as captured_labels,
        ):
            self.picking.button_validate()

        self.assertTrue(self.picking.state == "done")
        self.assertEqual(len(captured_messages.records), 2)
        self.assertIn(
            "Shipment created with colissimo_fr "
            "Tracking Numbers: TRACKING_NUMBER "
            f"Packages: {package.name}",
            captured_messages.records.mapped("preview"),
        )
        self.assertEqual(len(captured_labels.records), 1)
        label = captured_labels.records[0]
        self.assertEqual(label.package_id, package)
        self.assertEqual(package.carrier_id, self.delivery)
        self.assertEqual(package.parcel_tracking, "TRACKING_NUMBER")
        request = self._get_request(label.raw)
        self.assertEqual(request["contractNumber"], "colissimo_account")
        self.assertEqual(request["password"], "colissimo_password")
        self.assertEqual(request["letter"]["service"]["productCode"], "DOM")
        self.assertEqual(
            request["letter"]["service"]["depositDate"],
            (date.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
        )
        self.assertEqual(request["letter"]["parcel"]["weight"], 3.14)
        self.assertEqual(
            request["outputFormat"]["outputPrintingType"], "DPL_10x15_203dpi_UL"
        )
        self.assertEqual(
            request["letter"]["sender"]["address"]["companyName"],
            self.env.company.name,
        )
        self.assertEqual(
            request["letter"]["sender"]["address"]["line2"],
            "250 Executive Park Blvd, Suite",
        )
        self.assertEqual(request["letter"]["sender"]["address"]["line0"], "3400")
        self.assertEqual(
            request["letter"]["sender"]["address"]["city"], "San Francisco"
        )
        self.assertEqual(request["letter"]["sender"]["address"]["zipCode"], "94134")
        self.assertEqual(
            request["letter"]["addressee"]["address"]["lastName"], "Test Partner"
        )
        self.assertEqual(
            request["letter"]["addressee"]["address"]["line2"], "123 Test Street"
        )
        self.assertEqual(request["letter"]["addressee"]["address"]["city"], "Test City")
        self.assertEqual(request["letter"]["addressee"]["address"]["zipCode"], "12345")
        self.assertEqual(request["letter"]["addressee"]["address"]["countryCode"], "FR")
        self.assertEqual(
            request["letter"]["addressee"]["address"]["mobileNumber"], "123456789"
        )

    def test_get_label_from_picking_in_multiple_pack(self):
        self.product2 = self.env["product.product"].create(
            {
                "name": "Test Product 2",
                "type": "consu",
                "is_storable": True,
                "weight": 2.718,
                "default_code": "TEST456",
            }
        )
        self.env["sale.order.line"].create(
            {
                "product_id": self.product2.id,
                "product_uom_qty": 2,
                "order_id": self.order.id,
            }
        )
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": self.product2.id,
                "location_id": self.order.warehouse_id.lot_stock_id.id,
                "inventory_quantity": 2,
            },
        ).action_apply_inventory()

        self.order.action_confirm()
        self.picking = self.order.picking_ids
        self.assertEqual(len(self.picking.move_line_ids), 2)

        package1 = self.picking._put_in_pack(self.picking.move_line_ids[0])
        package2 = self.picking._put_in_pack(self.picking.move_line_ids[1])

        with (
            RecordCapturer(self.env["mail.message"], []) as captured_messages,
            RecordCapturer(self.env["shipping.label"], []) as captured_labels,
        ):
            self.picking.button_validate()
        self.assertTrue(self.picking.state == "done")
        self.assertEqual(len(captured_messages.records), 2)
        self.assertIn(
            "Shipment created with colissimo_fr "
            f"Tracking Numbers: TRACKING_NUMBER+TRACKING_NUMBER "
            f"Packages: {package1.name} and {package2.name}",
            captured_messages.records.mapped("preview"),
        )
        self.assertEqual(len(captured_labels.records), 2)
        label1 = captured_labels.records[0]
        label2 = captured_labels.records[1]
        self.assertEqual(label1.package_id, package1)
        self.assertEqual(label2.package_id, package2)
        self.assertEqual(package1.carrier_id, self.delivery)
        self.assertEqual(package1.parcel_tracking, "TRACKING_NUMBER")
        self.assertEqual(package2.carrier_id, self.delivery)
        self.assertEqual(package2.parcel_tracking, "TRACKING_NUMBER")
        request1 = self._get_request(label1.raw)
        request2 = self._get_request(label2.raw)
        for request in (request1, request2):
            self.assertEqual(request["contractNumber"], "colissimo_account")
            self.assertEqual(request["password"], "colissimo_password")
            self.assertEqual(request["letter"]["service"]["productCode"], "DOM")
            self.assertEqual(
                request["letter"]["service"]["depositDate"],
                (date.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
            )
            self.assertEqual(
                request["outputFormat"]["outputPrintingType"], "DPL_10x15_203dpi_UL"
            )
            self.assertEqual(
                request["letter"]["sender"]["address"]["companyName"],
                self.env.company.name,
            )
            self.assertEqual(
                request["letter"]["sender"]["address"]["line2"],
                "250 Executive Park Blvd, Suite",
            )
            self.assertEqual(request["letter"]["sender"]["address"]["line0"], "3400")
            self.assertEqual(
                request["letter"]["sender"]["address"]["city"], "San Francisco"
            )
            self.assertEqual(request["letter"]["sender"]["address"]["zipCode"], "94134")
            self.assertEqual(
                request["letter"]["addressee"]["address"]["lastName"], "Test Partner"
            )
            self.assertEqual(
                request["letter"]["addressee"]["address"]["line2"], "123 Test Street"
            )
            self.assertEqual(
                request["letter"]["addressee"]["address"]["city"], "Test City"
            )
            self.assertEqual(
                request["letter"]["addressee"]["address"]["zipCode"], "12345"
            )
            self.assertEqual(
                request["letter"]["addressee"]["address"]["countryCode"], "FR"
            )
            self.assertEqual(
                request["letter"]["addressee"]["address"]["mobileNumber"], "123456789"
            )

        self.assertEqual(request1["letter"]["parcel"]["weight"], 3.14)
        self.assertEqual(request2["letter"]["parcel"]["weight"], 5.44)

    def test_get_label_from_picking_half_packaged(self):
        self.product2 = self.env["product.product"].create(
            {
                "name": "Test Product 2",
                "type": "consu",
                "is_storable": True,
                "weight": 2.718,
                "default_code": "TEST456",
            }
        )
        self.env["sale.order.line"].create(
            {
                "product_id": self.product2.id,
                "product_uom_qty": 2,
                "order_id": self.order.id,
            }
        )
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": self.product2.id,
                "location_id": self.order.warehouse_id.lot_stock_id.id,
                "inventory_quantity": 2,
            },
        ).action_apply_inventory()

        self.order.action_confirm()
        self.picking = self.order.picking_ids
        self.assertEqual(len(self.picking.move_line_ids), 2)

        package = self.picking._put_in_pack(self.picking.move_line_ids[0])

        with (
            RecordCapturer(self.env["mail.message"], []) as captured_messages,
            RecordCapturer(self.env["shipping.label"], []) as captured_labels,
        ):
            self.picking.button_validate()
        self.assertTrue(self.picking.state == "done")
        self.assertEqual(len(captured_messages.records), 2)
        self.assertIn(
            "Shipment created with colissimo_fr "
            f"Tracking Numbers: TRACKING_NUMBER+TRACKING_NUMBER "
            f"Packages: {package.name} and Bulk Content",
            captured_messages.records.mapped("preview"),
        )
        self.assertEqual(len(captured_labels.records), 2)
        label1 = captured_labels.records[0]
        label2 = captured_labels.records[1]
        self.assertEqual(label1.package_id, package)
        self.assertFalse(label2.package_id)
        request1 = self._get_request(label1.raw)
        request2 = self._get_request(label2.raw)
        for request in (request1, request2):
            self.assertEqual(request["contractNumber"], "colissimo_account")
            self.assertEqual(request["password"], "colissimo_password")
            self.assertEqual(request["letter"]["service"]["productCode"], "DOM")
            self.assertEqual(
                request["letter"]["service"]["depositDate"],
                (date.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
            )
            self.assertEqual(
                request["outputFormat"]["outputPrintingType"], "DPL_10x15_203dpi_UL"
            )
            self.assertEqual(
                request["letter"]["sender"]["address"]["companyName"],
                self.env.company.name,
            )
            self.assertEqual(
                request["letter"]["sender"]["address"]["line2"],
                "250 Executive Park Blvd, Suite",
            )
            self.assertEqual(request["letter"]["sender"]["address"]["line0"], "3400")
            self.assertEqual(
                request["letter"]["sender"]["address"]["city"], "San Francisco"
            )
            self.assertEqual(request["letter"]["sender"]["address"]["zipCode"], "94134")
            self.assertEqual(
                request["letter"]["addressee"]["address"]["lastName"], "Test Partner"
            )
            self.assertEqual(
                request["letter"]["addressee"]["address"]["line2"], "123 Test Street"
            )
            self.assertEqual(
                request["letter"]["addressee"]["address"]["city"], "Test City"
            )
            self.assertEqual(
                request["letter"]["addressee"]["address"]["zipCode"], "12345"
            )
            self.assertEqual(
                request["letter"]["addressee"]["address"]["countryCode"], "FR"
            )
            self.assertEqual(
                request["letter"]["addressee"]["address"]["mobileNumber"], "123456789"
            )

        self.assertEqual(request1["letter"]["parcel"]["weight"], 3.14)
        self.assertEqual(request2["letter"]["parcel"]["weight"], 5.44)

    def test_get_label_from_picking_tracking_link(self):
        self.order.action_confirm()
        self.picking = self.order.picking_ids
        self.picking.button_validate()
        self.assertEqual(self.picking.carrier_tracking_ref, "TRACKING_NUMBER")
        self.assertEqual(
            self.picking.carrier_tracking_url,
            "https://www.laposte.fr/outils/suivre-vos-envois?code=TRACKING_NUMBER",
        )

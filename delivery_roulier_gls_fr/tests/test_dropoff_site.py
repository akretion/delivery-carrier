# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestDropOffSite(TransactionCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        ref = self.env.ref

        self.partner = self.env["res.partner"].create(
            {
                "name": "John Doe",
                "email": "john@doe.com",
                "country_id": 1,
            }
        )
        self.picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "carrier_id": ref(
                    "delivery_roulier_gls_fr.delivery_carrier_gls_shop"
                ).id,
                "picking_type_id": ref("stock.picking_type_out").id,
                "location_id": ref("stock.stock_location_stock").id,
                "location_dest_id": ref("stock.stock_location_customers").id,
            }
        )
        self.account = self.env.ref("delivery_roulier_gls_fr.carrier_account_gls")
        self.account.write({"account": "250test", "password": "250testpwd"})

    def test_service_payload(self):
        service = self.picking._get_service(self.account)
        self.assertEqual(service["product"], "shopdeliveryservice")
        self.assertEqual(service["pickupLocationId"], "")
        self.partner.dropoff_site = "ABC12345"
        service = self.picking._get_service(self.account)
        self.assertEqual(service["product"], "shopdeliveryservice")
        self.assertEqual(service["pickupLocationId"], "ABC12345")

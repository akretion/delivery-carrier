# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestDropOffSite(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = cls.env.ref
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.partner.id,
                "carrier_id": ref(
                    "delivery_roulier_gls_fr.delivery_carrier_gls_shop"
                ).id,
                "picking_type_id": ref("stock.picking_type_out").id,
                "location_id": ref("stock.stock_location_stock").id,
                "location_dest_id": ref("stock.stock_location_customers").id,
            }
        )
        cls.account = ref("delivery_roulier_gls_fr.carrier_account_gls")
        cls.account.write({"account": "250test", "password": "250testpwd"})

    def test_service_payload(self):
        service = self.picking._get_service(self.account)
        self.assertEqual(service["product"], "shopdeliveryservice")
        self.assertEqual(service["pickupLocationId"], "")
        self.partner.dropoff_site = "ABC12345"
        service = self.picking._get_service(self.account)
        self.assertEqual(service["product"], "shopdeliveryservice")
        self.assertEqual(service["pickupLocationId"], "ABC12345")

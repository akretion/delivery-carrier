# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64

from odoo.fields import Command
from odoo.modules.module import get_resource_path
from odoo.tests.common import TransactionCase


class TestKuehneNagel(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner1 = cls.env["res.partner"].create(
            {
                "name": "Test 1",
                "street": "39 rue du test",
                "city": "BOURNAZEL",
                "zip": "81170",
                "country_id": cls.env.ref("base.fr").id,
            }
        )
        cls.partner2 = cls.env["res.partner"].create(
            {
                "name": "Test 2",
                "street": "40 rue du test",
                "city": "AUSSILLON",
                "zip": "81200",
                "country_id": cls.env.ref("base.fr").id,
            }
        )
        company = cls.env.ref("base.main_company")
        company.write(
            {"siret": "79237773100023", "country_id": cls.env.ref("base.fr").id}
        )
        cls._import_directional_code(cls)
        cls.carrier = cls.env.ref(
            "delivery_roulier_kuehne_nagel_fr.kuehne_nagel_carrier"
        )

    def _import_directional_code(self):
        file_path = get_resource_path(
            "delivery_roulier_kuehne_nagel_fr", "tests/files/", "directional_codes.csv"
        )
        data = base64.b64encode(open(file_path, "rb").read())
        att = self.env["attachment.queue"].create(
            {
                "name": "directional_codes.csv",
                "datas": data,
                "file_type": "import_directional_code",
            }
        )
        att.button_manual_run()

    def test_kuehne_nagel_import_directional_code(self):
        codes = self.env["kuehne.directional.code"].search([])
        self.assertEqual(len(codes), 5)
        bournazel_code = codes.filtered(lambda c: c.city_to == "BOURNAZEL")
        self.assertTrue(bournazel_code)
        self.assertEqual(bournazel_code.first_zip, "81170")
        self.assertEqual(bournazel_code.office_round, "RI81")

    def _process_sale_order(self, sale):
        sale.action_confirm()
        delivery = sale.picking_ids
        delivery.move_ids.quantity_done = 1
        delivery.action_put_in_pack()
        delivery._action_done()

    def test_sale_delivery_with_kuehne_nagel(self):
        sale1 = self.env["sale.order"].create(
            {
                "partner_id": self.partner1.id,
                "carrier_id": self.carrier.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.env.ref(
                                "product.product_delivery_01"
                            ).id,
                        }
                    )
                ],
            }
        )
        sale2 = self.env["sale.order"].create(
            {
                "partner_id": self.partner2.id,
                "carrier_id": self.carrier.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.env.ref(
                                "product.product_delivery_01"
                            ).id,
                        }
                    )
                ],
            }
        )
        for sale in sale1 | sale2:
            self._process_sale_order(sale)
        delivery1 = sale.picking_ids
        self.assertEqual(
            delivery1.carrier_tracking_ref, delivery1.name.replace("/", "")
        )
        label1 = self.env["shipping.label"].search(
            [("res_id", "=", delivery1.id), ("res_model", "=", "stock.picking")]
        )
        self.assertEqual(len(label1), 1)
        self.assertTrue(delivery1.package_ids.parcel_tracking_uri)

        # test edi file
        deposit = self.env["deposit.slip"].create(
            {
                "delivery_type": "kuehne_nagel_fr",
                "picking_ids": [
                    Command.link(sale1.picking_ids.id),
                    Command.link(sale2.picking_ids.id),
                ],
            }
        )
        deposit.validate_deposit()
        edi_file = self.env["attachment.queue"].search(
            [("res_id", "=", deposit.id), ("res_model", "=", "deposit.slip")]
        )
        self.assertEqual(edi_file.file_type, "export")

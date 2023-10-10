# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestGetWeight(TransactionCase):
    """Test get_weight functions."""

    # some helpers
    def _create_order(self, customer):
        return self.env["sale.order"].create({"partner_id": customer.id})

    def _create_order_line(self, order, products):
        for product in products:
            self.env["sale.order.line"].create(
                {"product_id": product.id, "order_id": order.id}
            )

    def _create_ul(self):
        vals = [
            {"name": "Cardboard box", "type": "box", "weight": 0.200},
            {"name": "Wood box", "type": "box", "weight": 1.30},
        ]

        return [self.env["product.ul"].create(val) for val in vals]

    def _create_operation(self, picking, values):
        vals = {
            "picking_id": picking.id,
            "location_id": picking.location_id.id,
            "location_dest_id": picking.location_dest_id.id,
        }
        vals.update(values)
        return self.env["stock.move.line"].create(vals)

    def _create_product(self, vals):
        return self.env["product.product"].create(vals)

    def _get_products(self, weights):
        """A recordset of products without any specific uom.

        It means : no uom or kg or unit
        Params:
            weights: recordset will be size of weights and each
                product will get a size according of weights[i]
        """
        kg_id = self.env.ref("uom.product_uom_kgm").id
        unit_id = self.env.ref("uom.product_uom_unit").id

        products = self.env["product.product"].search(
            [["uom_id", "in", (False, kg_id, unit_id)]], limit=len(weights)
        )
        for idx, product in enumerate(products):
            # by default there is no weight on products
            product.weight = weights[idx]
        return products

    def _generate_picking(self, products):
        """Create a picking from products."""
        customer = self.env["res.partner"].search([], limit=1)
        order = self._create_order(customer)
        self._create_order_line(order, products)
        order.action_confirm()
        picking = order.picking_ids
        picking.button_validate()
        return picking

    def test_get_weight(self):
        """Test quant.package.weight computed field and
        pack.operation.get_weight."""
        # prepare some data
        weights = [2, 30, 1, 24, 39]
        products = self._get_products(weights)
        picking = self._generate_picking(products)
        package = self.env["stock.quant.package"].create({})
        operations = self.env["stock.move.line"]
        for product in products:
            operations |= self._create_operation(
                picking,
                {
                    "reserved_uom_qty": 1,
                    "product_id": product.id,
                    "product_uom_id": product.uom_id.id,
                    "result_package_id": package.id,
                },
            )
        # end of prepare data

        # test operation.get_weight()
        for operation in operations:
            self.assertEqual(
                operation.get_weight(),
                operation.product_id.weight * operation.reserved_uom_qty,
            )

        # test package.weight
        self.assertEqual(package.weight, sum(product.weight for product in products))

    def test_total_weight(self):
        """Test quant.package.weight computed field when a total
        weight is defined"""
        # prepare some data
        weights = [2, 30, 1, 24, 39]
        products = self._get_products(weights)
        picking = self._generate_picking(products)
        package = self.env["stock.quant.package"].create({})
        operations = self.env["stock.move.line"]
        for product in products:
            operations |= self._create_operation(
                picking,
                {
                    "reserved_uom_qty": 1,
                    "product_id": product.id,
                    "product_uom_id": product.uom_id.id,
                    "result_package_id": package.id,
                },
            )
        package.shipping_weight = 1542.0
        # end of prepare data

        # test operation.get_weight()
        for operation in operations:
            self.assertEqual(
                operation.get_weight(),
                operation.product_id.weight * operation.reserved_uom_qty,
            )

        # test package.weight
        self.assertEqual(package.weight, package.shipping_weight)

    def test_get_weight_with_qty(self):
        """Ensure qty are taken in account."""
        # prepare some data
        weights = [2, 30, 1, 24, 39]
        products = self._get_products(weights)
        picking = self._generate_picking(products)
        package = self.env["stock.quant.package"].create({})
        operations = self.env["stock.move.line"]
        for idx, product in enumerate(products):
            operations |= self._create_operation(
                picking,
                {
                    "reserved_uom_qty": idx,  # nice one
                    "product_id": product.id,
                    "product_uom_id": product.uom_id.id,
                    "result_package_id": package.id,
                },
            )
        # end of prepare data

        # test operation.get_weight()
        for operation in operations:
            self.assertEqual(
                operation.get_weight(),
                operation.product_id.weight * operation.reserved_uom_qty,
            )

        # test package._weight
        self.assertEqual(
            package.weight, sum(operation.get_weight() for operation in operations)
        )

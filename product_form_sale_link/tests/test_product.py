from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProductSalesCount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test users with different access rights
        sale_manager_group = cls.env.ref("sales_team.group_sale_manager")
        sale_user_group = cls.env.ref("sales_team.group_sale_salesman")
        product_manager_group = cls.env.ref("product.group_product_manager")

        cls.user_salesman = cls.env["res.users"].create(
            {
                "name": "Test Salesman",
                "login": "test_salesman",
                "email": "test_salesman@example.com",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            sale_manager_group.id,
                            sale_user_group.id,
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("base.group_partner_manager").id,
                        ],
                    )
                ],
            }
        )

        cls.user_employee = cls.env["res.users"].create(
            {
                "name": "Test Employee",
                "login": "test_employee",
                "email": "test_employee@example.com",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            product_manager_group.id,
                        ],
                    )
                ],
            }
        )

        cls.currency = cls.env["res.currency"].create(
            {
                "name": "Test Currency",
                "symbol": "T€",
                "rate": 1.0,
            }
        )

        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test Pricelist",
                "currency_id": cls.currency.id,
            }
        )

        cls.product_template = cls.env["product.template"].create(
            {
                "name": "Test Product Template",
                "list_price": 100.0,
                "taxes_id": False,
                "currency_id": cls.currency.id,
            }
        )

        cls.size_attribute = cls.env["product.attribute"].create(
            {
                "name": "Size",
                "create_variant": "always",
            }
        )

        cls.size_s = cls.env["product.attribute.value"].create(
            {
                "name": "S",
                "attribute_id": cls.size_attribute.id,
            }
        )

        cls.size_m = cls.env["product.attribute.value"].create(
            {
                "name": "M",
                "attribute_id": cls.size_attribute.id,
            }
        )

        cls.env["product.template.attribute.line"].create(
            {
                "product_tmpl_id": cls.product_template.id,
                "attribute_id": cls.size_attribute.id,
                "value_ids": [(6, 0, [cls.size_s.id, cls.size_m.id])],
            }
        )

        cls.product_variant1, cls.product_variant2 = (
            cls.product_template.product_variant_ids
        )

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "email": "test@example.com",
            }
        )

        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "pricelist_id": cls.pricelist.id,
            }
        )

    def test_product_variant_sales_count_with_salesman(self):
        """Test sales count computation for product variants with salesman access"""
        self.sale_order.action_confirm()

        # Switch to salesman user and check counts
        product = self.product_variant1.with_user(self.user_salesman)
        product._compute_sale_lines_count()

        self.assertEqual(product.sale_lines_count, 0)
        self.assertEqual(
            self.product_variant2.with_user(self.user_salesman).sale_lines_count, 0
        )

    def test_product_variant_sales_count_without_access(self):
        """Test sales count computation for product variants without salesman access"""

        self.sale_order.action_confirm()

        # Switch to employee user and check counts
        product = self.product_variant1.with_user(self.user_employee)
        product._compute_sale_lines_count()

        self.assertEqual(product.sale_lines_count, 0)

    def test_product_template_sales_count(self):
        """Test sales count computation for product template"""
        self.env["sale.order.line"].create(
            [
                {
                    "order_id": self.sale_order.id,
                    "product_id": self.product_variant1.id,
                    "product_uom_qty": 1.0,
                    "price_unit": 100.0,
                },
                {
                    "order_id": self.sale_order.id,
                    "product_id": self.product_variant2.id,
                    "product_uom_qty": 1.0,
                    "price_unit": 100.0,
                },
            ]
        )

        self.sale_order.action_confirm()

        template = self.product_template.with_user(self.user_salesman)
        template._compute_sale_lines_count()

        self.assertEqual(template.sale_lines_count, 2)

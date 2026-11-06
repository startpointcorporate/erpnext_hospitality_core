"""Regression for invoice submission on a newly installed Hospitality site."""
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from hospitality_core.api.composite_item_utils import process_composite_items_in_invoice


class TestCompositeItemInstallSchema(IntegrationTestCase):
    def test_install_migrate_provides_item_flag(self):
        self.assertTrue(frappe.db.has_column("Item", "is_composite_item"))
        field = frappe.get_meta("Item").get_field("is_composite_item")
        self.assertEqual(field.fieldtype, "Check")
        self.assertEqual(str(field.default), "0")

    def test_plain_item_invoice_hook_does_not_query_missing_column(self):
        item = frappe.get_doc(dict(doctype="Item", item_code="schema-"+uuid4().hex[:12],
            item_name="Schema regression", item_group="Services", stock_uom="Nos", is_stock_item=0)).insert()
        invoice = frappe.new_doc("Sales Invoice")
        invoice.append("items", dict(item_code=item.name, qty=1))
        process_composite_items_in_invoice(invoice)
        self.assertFalse(frappe.db.get_value("Item", item.name, "is_composite_item"))

# Copyright (c) 2026, Gift Braimah and Contributors
# See license.txt
"""Run with bench --site <test-site> run-tests --doctype 'Guest Folio'."""
import unittest

import frappe
from frappe.model.document import Document
from frappe.permissions import add_permission, update_permission_property

from hospitality_core.hospitality_core.doctype.guest_folio.guest_folio import GuestFolio


class TestGuestFolio(unittest.TestCase):
    def setUp(self):
        self.previous_user = frappe.session.user
        frappe.set_user("Administrator")
        frappe.db.savepoint("guest_folio_permissions")
        self.addCleanup(self.cleanup_permissions)
        self.visitor_role = "_Test Folio Visitor"
        frappe.get_doc({"doctype": "Role", "role_name": self.visitor_role}).insert()
        add_permission("Guest Folio", self.visitor_role, ptype="read")
        update_permission_property("Guest Folio", self.visitor_role, 0, "write", 1)
        update_permission_property("Guest Folio", self.visitor_role, 0, "create", 1)
        for permission in ("export", "delete", "share", "email", "print", "report"):
            update_permission_property("Guest Folio", self.visitor_role, 0, permission, 0)
        self.hospitality = self.make_user("hospitality", "Hospitality User")
        self.other = self.make_user("other", "Hospitality User")
        self.visitor = self.make_user("visitor", self.visitor_role)
        self.unprivileged = self.make_user("unprivileged")
        self.manager = self.make_user("manager", "System Manager")
        self.folio = frappe.get_doc({"doctype": "Guest Folio", "status": "Open",
                                     "reserved_by": self.other}).insert()
        # Check a normally loaded document, never ignore_permissions flags.
        self.folio = frappe.get_doc("Guest Folio", self.folio.name)

    def make_user(self, name, role=None):
        user = frappe.get_doc({"doctype": "User", "email": f"_test_folio_{name}@example.com",
                              "first_name": name, "send_welcome_email": 0,
                              "user_type": "System User"})
        if role:
            user.append("roles", {"role": role})
        user.insert()
        return user.name

    def cleanup_permissions(self):
        frappe.set_user("Administrator")
        frappe.db.rollback(save_point="guest_folio_permissions")
        frappe.clear_cache()
        frappe.set_user(self.previous_user)

    def test_inherits_standard_permission_contract(self):
        self.assertIs(GuestFolio.has_permission, Document.has_permission)
        self.assertTrue(self.folio.has_permission("read", user=self.hospitality, debug=True))
        self.assertTrue(self.folio.has_permission(user="Administrator"))

    def test_hospitality_permissions_follow_docperm(self):
        for permission in ("read", "write", "create", "export"):
            with self.subTest(permission=permission):
                self.assertTrue(self.folio.has_permission(permission, user=self.hospitality))
        self.assertFalse(self.folio.has_permission("delete", user=self.hospitality))
        update_permission_property("Guest Folio", "Hospitality User", 0, "export", 0)
        self.assertFalse(self.folio.has_permission("export", user=self.hospitality))
        self.assertTrue(self.folio.has_permission("read", user=self.hospitality))

    def test_custom_visitor_role_and_folio_flow(self):
        frappe.set_user(self.visitor)
        self.assertTrue(self.folio.has_permission("read"))
        self.assertTrue(self.folio.has_permission("write"))
        self.assertFalse(self.folio.has_permission("export"))
        self.assertFalse(self.folio.has_permission("delete"))
        created = frappe.get_doc({"doctype": "Guest Folio", "status": "Open",
                                  "reserved_by": self.visitor}).insert()
        created.reload()
        created.status = "Provisional"
        created.save()
        self.assertEqual(frappe.get_doc("Guest Folio", created.name).status, "Provisional")
        with self.assertRaises(frappe.PermissionError):
            frappe.delete_doc("Guest Folio", created.name)

    def test_custom_read_only_role_cannot_write_or_create(self):
        update_permission_property("Guest Folio", self.visitor_role, 0, "write", 0)
        update_permission_property("Guest Folio", self.visitor_role, 0, "create", 0)
        self.assertTrue(self.folio.has_permission("read", user=self.visitor))
        for permission in ("write", "create", "export", "delete"):
            with self.subTest(permission=permission):
                self.assertFalse(self.folio.has_permission(permission, user=self.visitor))
        frappe.set_user(self.visitor)
        self.folio.status = "Provisional"
        with self.assertRaises(frappe.PermissionError):
            self.folio.save()

    def test_unprivileged_and_guest_users_are_denied(self):
        for user in (self.unprivileged, "Guest"):
            for permission in ("read", "write", "create", "export", "delete"):
                with self.subTest(user=user, permission=permission):
                    self.assertFalse(self.folio.has_permission(permission, user=user))

    def test_system_manager_obeys_custom_permissions(self):
        self.assertTrue(self.folio.has_permission("delete", user=self.manager))
        update_permission_property("Guest Folio", "System Manager", 0, "delete", 0)
        self.assertFalse(self.folio.has_permission("delete", user=self.manager))
        self.assertTrue(self.folio.has_permission("read", user=self.manager))

    def test_reserved_by_is_audit_metadata_not_an_access_boundary(self):
        frappe.get_doc({"doctype": "User Permission", "user": self.hospitality,
                        "allow": "User", "for_value": self.hospitality,
                        "applicable_for": "Guest Folio", "apply_to_all_doctypes": 0}).insert()
        frappe.clear_cache(user=self.hospitality)
        self.assertNotEqual(self.folio.reserved_by, self.hospitality)
        self.assertTrue(self.folio.meta.get_field("reserved_by").ignore_user_permissions)
        self.assertTrue(self.folio.has_permission("read", user=self.hospitality))
        self.assertTrue(self.folio.has_permission("write", user=self.hospitality))
        self.assertIn(self.folio.name, frappe.get_list("Guest Folio", pluck="name", user=self.hospitality))

    def test_explicit_folio_user_permissions_remain_enforced(self):
        allowed = frappe.get_doc({"doctype": "Guest Folio", "status": "Open"}).insert()
        frappe.get_doc({"doctype": "User Permission", "user": self.hospitality,
                        "allow": "Guest Folio", "for_value": allowed.name,
                        "apply_to_all_doctypes": 1}).insert()
        frappe.clear_cache(user=self.hospitality)
        self.assertTrue(allowed.has_permission("read", user=self.hospitality))
        self.assertFalse(self.folio.has_permission("read", user=self.hospitality))
        self.assertFalse(self.folio.has_permission("write", user=self.hospitality))

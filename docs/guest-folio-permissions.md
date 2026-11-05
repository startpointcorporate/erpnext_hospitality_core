# Guest Folio permissions

Guest Folio inherits `Document.has_permission`, including its native signature,
role permissions, Custom DocPerm, User Permission, sharing and Administrator
semantics. Hospitality User retains read/write/create/export as declared in the
DocType, and cannot delete. A custom role receives only the rights configured by
an administrator. System Manager no longer bypasses customized permissions.

`reserved_by` is a read-only audit link, not an ownership boundary. Its native
`ignore_user_permissions` flag prevents a receptionist's User restriction from
hiding folios reserved by a colleague. Explicit Guest Folio restrictions and all
other business link restrictions remain enforced. No global User Permission
bypass or role allowlist is introduced.

After the normal application update, run `bench --site <site> migrate` to reload
the field metadata. No demo-specific code or role is included in this application.

Run on an isolated Frappe test site with ERPNext and Hospitality Core installed:

```bash
bench --site <test-site> run-tests --module hospitality_core.hospitality_core.doctype.guest_folio.test_guest_folio
```

Eight regression tests cover the inherited contract, Hospitality User, custom
visitor/read-only roles, real insert/save/delete checks, export revocation,
System Manager customization, Guest/no-role denial, colleagues' folios and
explicit folio User Permissions. Tests use transaction savepoints and clear
permission caches after rollback. Do not run the suite against production sites.

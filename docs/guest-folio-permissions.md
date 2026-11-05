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

## Standard image validation — 2026-11-05

The eight tests pass on the standard AMD64 candidate
`docker.io/konektag/erpnext:v16.53.0-custom-validation-20261105-r2`, digest
`sha256:a72dce05cf0346b949723854defeeb237d2402d46550cbc8d430f33e8e01ae7e`.
The image embeds this PR's application code at
`9ac71b36625bf555b5e3739facd8c4e89761a316`, Frappe 16.54.0 and ERPNext 16.53.0.
Tests ran against disposable MariaDB 11.8 with the native application installed
from the image, without an application source mount. The HTTP acceptance suite
and official-site copies are maintained in konektag-infra PR #7; standard build,
source locking and promotion gates are in PR #8. No production migration,
promotion or PR merge was performed. The application code remains unchanged
by this validation documentation update.

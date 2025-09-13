# HR Gate Pass (v18)

Initial MVP implementing Gate Pass lifecycle: create, approve, issue, QR, basic scan endpoint, and PDF report.

- Pass types: employee_out, visitor, material, vehicle, contractor
- States: draft, to_approve, approved, issued, checked_out, returned, closed, rejected, cancel
- QR token generation using HMAC with database uuid
- Basic security groups and menus

This is a foundation to extend with full approval profiles, record rules, guard UI, and integrations.

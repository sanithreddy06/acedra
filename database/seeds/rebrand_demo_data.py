"""
Bring an EXISTING development database's synthetic demo rows in line with the ACEDRA brand.

Only rows created by the synthetic seed are touched, and the change is reversible: it renames
brand strings, so no records are added or removed.
  * synthetic RIO staff logins   @rio-platform.example  ->  @acedra.example
  * employee codes               RIO-0001               ->  ACD-0001
  * role display names           "RIO Super Administrator" -> "ACEDRA Super Administrator"
  * seeded agreement references  RIO-SA-2026-00x       ->  ACD-SA-2026-00x  (enquiries + universities)

Historical text (audit logs, email outbox, enquiry activity notes) is left exactly as recorded.

Usage (from the repository root):
    python database/seeds/rebrand_demo_data.py          # dry run: shows what would change
    python database/seeds/rebrand_demo_data.py --apply  # apply
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402

CHANGES = [
    ("synthetic staff emails",
     "SELECT count(*) FROM users WHERE is_synthetic = :t AND email LIKE '%@rio-platform.example'",
     "UPDATE users SET email = REPLACE(email, '@rio-platform.example', '@acedra.example') "
     "WHERE is_synthetic = :t AND email LIKE '%@rio-platform.example'"),
    ("employee codes",
     "SELECT count(*) FROM employee_profiles WHERE employee_code LIKE 'RIO-%'",
     "UPDATE employee_profiles SET employee_code = 'ACD-' || SUBSTR(employee_code, 5) WHERE employee_code LIKE 'RIO-%'"),
    ("role display names",
     "SELECT count(*) FROM roles WHERE display_name LIKE 'RIO %'",
     "UPDATE roles SET display_name = 'ACEDRA ' || SUBSTR(display_name, 5) WHERE display_name LIKE 'RIO %'"),
    ("role descriptions",
     "SELECT count(*) FROM roles WHERE description LIKE 'RIO %'",
     "UPDATE roles SET description = 'ACEDRA ' || SUBSTR(description, 5) WHERE description LIKE 'RIO %'"),
    ("enquiry agreement references",
     "SELECT count(*) FROM enquiries WHERE agreement_reference LIKE 'RIO-SA-%'",
     "UPDATE enquiries SET agreement_reference = 'ACD-SA-' || SUBSTR(agreement_reference, 8) WHERE agreement_reference LIKE 'RIO-SA-%'"),
    ("university agreement references",
     "SELECT count(*) FROM universities WHERE is_synthetic = :t AND agreement_reference LIKE 'RIO-SA-%'",
     "UPDATE universities SET agreement_reference = 'ACD-SA-' || SUBSTR(agreement_reference, 8) "
     "WHERE is_synthetic = :t AND agreement_reference LIKE 'RIO-SA-%'"),
]


def main() -> None:
    apply = "--apply" in sys.argv
    print(f"Database: {engine.url.render_as_string(hide_password=True)}  ({'APPLY' if apply else 'dry run'})")
    with engine.begin() as conn:
        for label, count_sql, update_sql in CHANGES:
            n = conn.execute(text(count_sql), {"t": True}).scalar() or 0
            print(f"  {label:32s} {n:3d} row(s)")
            if apply and n:
                conn.execute(text(update_sql), {"t": True})
    if not apply:
        print("No changes made. Re-run with --apply to update.")


if __name__ == "__main__":
    main()

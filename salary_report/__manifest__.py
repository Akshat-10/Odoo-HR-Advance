{
    "name": "Salary Report",
    "version": "18.0.1.0.0",
    "category": "Human Resources",
    "summary": "Salary Report Wizard",
    "depends": ["hr", "hr_payroll", 'l10n_in_hr_payroll', 'hr_employee_entended', 'payroll_salary_link',],
    "data": [
        "security/ir.model.access.csv",
        "views/salary_report_wizard_view.xml",
        "views/nomination_form_views.xml",
    ],
    "application": True,
    "installable": True,
}

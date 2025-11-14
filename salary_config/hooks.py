# -*- coding: utf-8 -*-
def post_init_hook(env):
    """Migrate salary_config code references to payroll salary rule categories."""
    Category = env['hr.salary.rule.category']

    existing_categories = {
        (cat.code or '').strip(): cat
        for cat in Category.search([])
        if cat.code
    }

    def _get_or_create_category(name, code):
        code_key = (code or '').strip()
        if not code_key:
            return False
        category = existing_categories.get(code_key)
        if not category:
            category = Category.search([('code', '=', code_key)], limit=1)
        if not category and name:
            category = Category.search([('name', '=', name)], limit=1)
        if not category:
            category = Category.create({'name': name or code_key, 'code': code_key})
        existing_categories[code_key] = category
        return category

    cr = env.cr
    cr.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = current_schema()
              AND table_name = 'salary_config_code'
        )
        """
    )
    if cr.fetchone()[0]:
        cr.execute("SELECT name, code FROM salary_config_code")
        for name, code in cr.fetchall():
            _get_or_create_category(name, code)

    def _assign_categories(model_name):
        model = env[model_name]
        for line in model.search([]):
            code_key = (line['code'] or '').strip()
            name = line['name'] or ''
            if not code_key:
                continue
            category = existing_categories.get(code_key)
            if not category:
                category = _get_or_create_category(name, code_key)
            current_category = line['code_id']
            if category and current_category and current_category.id == category.id:
                continue
            if category:
                line.write({'code_id': category.id})

    _assign_categories('salary.config.structure.line')
    _assign_categories('hr.contract.salary.offer.structure.line')

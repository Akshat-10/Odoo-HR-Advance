# -*- coding: utf-8 -*-
def post_init_hook(env):
    _sync_salary_categories(env)
    _sync_salary_rules(env)


def _sync_salary_categories(env):
    CodeModel = env.get('salary.config.code')
    if not CodeModel:
        return

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

    for record in CodeModel.search_read([], ['name', 'code']):
        _get_or_create_category(record.get('name'), record.get('code'))

    def _assign_categories(model_name):
        model = env[model_name]
        for line in model.search([]):
            code_val = getattr(line, 'code', False)
            name_val = getattr(line, 'name', False)
            category_val = getattr(line, 'code_id', False)
            code_key = str(code_val or '').strip()
            name = name_val or ''
            if not code_key:
                continue
            category = existing_categories.get(code_key)
            if not category:
                category = _get_or_create_category(name, code_key)
            if category and category_val != category:
                line.write({'code_id': category.id})

    _assign_categories('salary.config.structure.line')
    _assign_categories('hr.contract.salary.offer.structure.line')


def _sync_salary_rules(env):
    if 'salary.config.structure.line' not in env:
        return
    lines = env['salary.config.structure.line'].search([])
    if lines:
        lines._sync_hr_salary_rules()

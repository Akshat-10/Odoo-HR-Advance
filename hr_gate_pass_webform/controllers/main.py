# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

class GatePassWebformController(http.Controller):
    """Public website form for creating Gate Pass requests."""

    @http.route(['/gatepass/request'], type='http', auth='public', website=True, sitemap=True)
    def gatepass_request_form(self, **kwargs):
        env = request.env
        # Provide limited lists for selection
        pass_types = [
            ('visitor', _('Visitor')),
            ('vehicle', _('Vehicle')),
            ('material', _('Material')),
            ('contractor', _('Contractor')),
            ('employee_out', _('Employee Out')),
        ]
        employees = env['hr.employee'].sudo().search([], limit=50)
        gates = env['hr.gate'].sudo().search([], limit=50)
        representing_options = env['hr.gate.representing'].sudo().search([], limit=50)
        idno_options = env['hr.gate.idno'].sudo().search([], limit=50)
        departments = env['hr.department'].sudo().search([], limit=100)
        return request.render('hr_gate_pass_webform.template_gate_pass_form', {
            'pass_types': pass_types,
            'employees': employees,
            'gates': gates,
            'representing_options': representing_options,
            'idno_options': idno_options,
            'departments': departments,
            'values': {},
        })

    @http.route(['/gatepass/employee/<int:emp_id>/department'], type='http', auth='public', methods=['GET'], csrf=False)
    def gatepass_employee_department(self, emp_id, **kwargs):
        emp = request.env['hr.employee'].sudo().browse(emp_id)
        if not emp.exists():
            return request.make_response('{"department": "", "department_id": false}', headers=[('Content-Type', 'application/json')])
        dept = emp.department_id
        name = dept.name or ''
        return request.make_response('{"department": "%s", "department_id": %s}' % (name.replace('"','\"'), dept.id or 'false'), headers=[('Content-Type', 'application/json')])

    @http.route(['/gatepass/request/submit'], type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def gatepass_request_submit(self, **post):
        env = request.env
        vals = {}
        errors = []

        def _get(key):
            return (post.get(key) or '').strip()

        pass_type = _get('pass_type') or 'visitor'
        if pass_type not in ['visitor','vehicle','material','contractor','employee_out']:
            errors.append(_('Invalid pass type selected.'))
        vals['pass_type'] = pass_type

        reason = _get('reason')
        if not reason:
            errors.append(_('Reason is required.'))
        vals['reason'] = reason

        # Department select (public safe subset) direct parsing
        dept_id = _get('department_id')
        if dept_id.isdigit():
            vals['department_id'] = int(dept_id)

        # Host employee required for visitor pass (and used to auto-set department when not selected manually)
        host_employee_id = _get('host_employee_id')
        if pass_type == 'visitor' and not host_employee_id:
            errors.append(_('Host Employee is required for Visitor pass.'))
        if host_employee_id and host_employee_id.isdigit():
            vals['host_employee_id'] = int(host_employee_id)
            # Auto assign department from host employee
            if not vals.get('department_id'):
                emp = env['hr.employee'].sudo().browse(int(host_employee_id))
                if emp and emp.exists() and emp.department_id:
                    vals['department_id'] = emp.department_id.id

        gate_id = _get('gate_id')
        if gate_id and gate_id.isdigit():
            vals['gate_id'] = int(gate_id)

        # Visitor specific fields
        visitor_name = _get('visitor_name')
        visitor_contact = _get('visitor_contact')
        visitor_company = _get('visitor_company')
        id_proof_type = _get('id_proof_type')
        if pass_type == 'visitor':
            # Mandatory for visitor per updated spec: Representing From & Representing From (Details - now free text)
            if not _get('representing_from'):
                errors.append(_('Representing From is required.'))
            if not _get('representing_from_text'):
                errors.append(_('Representing From (Details) is required.'))
            # Visitor name/contact/company optional
            if visitor_name:
                vals['visitor_name'] = visitor_name
            if visitor_contact:
                vals['visitor_contact'] = visitor_contact
            if visitor_company:
                vals['visitor_company'] = visitor_company
            if id_proof_type:
                vals['id_proof_type'] = id_proof_type
        elif pass_type == 'contractor':
            # Contractor basic name optional per new spec (only visit type mandatory)
            vals['visitor_name'] = visitor_name
            vals['visitor_contact'] = visitor_contact
            vals['visitor_company'] = visitor_company

        # Vehicle (now optional fields even for vehicle pass type)
        vehicle_no = _get('vehicle_no')
        driver_name = _get('driver_name')
        if vehicle_no:
            vals['vehicle_no'] = vehicle_no
        if driver_name:
            vals['driver_name'] = driver_name

        # Employee Out specifics
        travel_to = _get('travel_to')
        employee_out_reason = _get('employee_out_reason')
        if pass_type == 'employee_out':
            if not employee_out_reason:
                errors.append(_('Employee Out Reason is required.'))
            vals['employee_out_reason'] = employee_out_reason
            # travel_to only required if official + vehicle required handled later
            vals['travel_to'] = travel_to

        # Material type minimal (list of items not supported in simple form - could be extended)
        # Make returnable optional
        is_returnable = _get('is_returnable') == 'on'
        vals['is_returnable'] = is_returnable
        if is_returnable:
            expected_return_raw = _get('expected_return_date') or _get('expected_return_datetime')
            if not expected_return_raw:
                errors.append(_('Expected return date/time required for returnable pass.'))
            else:
                parsed = False
                # Try direct odoo parse
                try:
                    vals['expected_return_datetime'] = fields.Datetime.to_datetime(expected_return_raw)
                    parsed = True
                except Exception:
                    pass
                # Try common HTML datetime-local format: YYYY-MM-DDTHH:MM
                if not parsed:
                    from datetime import datetime
                    for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d'):  # fallback date only
                        try:
                            dt = datetime.strptime(expected_return_raw, fmt)
                            # If date only, set time to 23:59 to cover whole day
                            if fmt == '%Y-%m-%d':
                                from datetime import time
                                dt = dt.replace(hour=23, minute=59, second=0)
                            # Convert to UTC aware via Odoo (assumes user timezone) -> use context_timestamp reverse if needed
                            vals['expected_return_datetime'] = fields.Datetime.to_string(dt)
                            parsed = True
                            break
                        except Exception:
                            continue
                if not parsed:
                    errors.append(_('Invalid expected return date.'))

        if errors:
            return request.render('hr_gate_pass_webform.template_gate_pass_form', {
                'errors': errors,
                'values': post,
                'pass_types': [('visitor','Visitor'),('vehicle','Vehicle'),('material','Material'),('contractor','Contractor'),('employee_out','Employee Out')],
                'employees': env['hr.employee'].sudo().search([], limit=50),
                'gates': env['hr.gate'].sudo().search([], limit=50),
                'representing_options': env['hr.gate.representing'].sudo().search([], limit=50),
                'idno_options': env['hr.gate.idno'].sudo().search([], limit=50),
            })

        # Extra optional/advanced fields parsing
        contractor_visit_type = _get('contractor_visit_type')
        if pass_type == 'contractor':
            if not contractor_visit_type:
                errors.append(_('Contractor Visit Type is required.'))
            else:
                vals['contractor_visit_type'] = contractor_visit_type

        area_of_visit = _get('area_of_visit')
        if area_of_visit:
            vals['area_of_visit'] = area_of_visit

        representing_from = _get('representing_from')
        if representing_from:
            vals['representing_from'] = representing_from

        # Many2many style inputs (expected either list or comma string)
        def _m2m_list(raw):
            if not raw:
                return []
            if isinstance(raw, (list, tuple)):
                return [int(x) for x in raw if str(x).isdigit()]
            return [int(x) for x in str(raw).split(',') if x.isdigit()]

        # Representing details now a free text field
        rep_text = _get('representing_from_text')
        if rep_text:
            vals['representing_from_text'] = rep_text

        emp_raw = request.httprequest.form.getlist('employee_ids') if request.httprequest else post.get('employee_ids')
        employee_ids_m2m = _m2m_list(emp_raw)
        if employee_ids_m2m:
            vals['employee_ids'] = [(6, 0, employee_ids_m2m)]

        # Single ID No. selection
        id_no_id = _get('id_no_id')
        if id_no_id and id_no_id.isdigit():
            vals['id_no_id'] = int(id_no_id)

        # id_proof_type removed from web form per request (ignore if posted)

        # Start datetime override
        start_dt = _get('start_datetime')
        if start_dt:
            try:
                vals['start_datetime'] = fields.Datetime.to_datetime(start_dt)
            except Exception:
                vals['start_datetime'] = fields.Datetime.now()
        else:
            vals['start_datetime'] = fields.Datetime.now()

        # Official vehicle required
        vals['official_vehicle_required'] = _get('official_vehicle_required') == 'on'
        if pass_type == 'employee_out' and employee_out_reason == 'official' and vals['official_vehicle_required']:
            if not travel_to:
                errors.append(_('Travel To is required when official vehicle is required.'))
            else:
                vals['travel_to'] = travel_to

        # Image binary
        image_file = post.get('image')
        if image_file and hasattr(image_file, 'read'):
            try:
                import base64
                vals['image'] = base64.b64encode(image_file.read())
            except Exception:
                pass

        # Create record first so we can link attachment(s)
        if errors:
            return request.render('hr_gate_pass_webform.template_gate_pass_form', {
                'errors': errors,
                'values': post,
                'pass_types': [('visitor','Visitor'),('vehicle','Vehicle'),('material','Material'),('contractor','Contractor'),('employee_out','Employee Out')],
                'employees': env['hr.employee'].sudo().search([], limit=50),
                'gates': env['hr.gate'].sudo().search([], limit=50),
                'representing_options': env['hr.gate.representing'].sudo().search([], limit=50),
                'idno_options': env['hr.gate.idno'].sudo().search([], limit=50),
            })

        rec = env['hr.gate.pass'].sudo().create(vals)

        # ID Proof attachment (single)
        id_proof_file = post.get('id_proof_attachment')
        if id_proof_file and hasattr(id_proof_file, 'filename') and id_proof_file.filename:
            try:
                import base64
                att_vals = {
                    'name': id_proof_file.filename,
                    'datas': base64.b64encode(id_proof_file.read()),
                    'res_model': 'hr.gate.pass',
                    'res_id': rec.id,
                    'type': 'binary',
                    'mimetype': getattr(id_proof_file, 'mimetype', 'application/octet-stream'),
                }
                attachment = env['ir.attachment'].sudo().create(att_vals)
                if attachment:
                    rec.id_proof_attachment_id = [(4, attachment.id)]
            except Exception:
                # Non-fatal; continue
                pass

        # NOTE: Auto submit removed so record stays in Draft allowing internal users to edit
        # Many2many fields (Representing From Details, Employees, ID No.) before approval.
        # If you want the previous behaviour (auto submit) toggle the code below.
        # Auto-submit so the record moves from 'draft' to 'to_approve' immediately after creation
        # (User requested status to be 'to_approve' instead of staying in draft.)
        try:
            rec.sudo().action_submit()
        except Exception:
            # Fail silently; record will remain in draft if transition fails
            pass

        # Send acknowledgment email if visitor_name and maybe contact
        template = env.ref('hr_gate_pass_webform.mail_template_gate_pass_public_submit', raise_if_not_found=False)
        if template and visitor_name and EMAIL_RE.match(visitor_contact or ''):
            template.sudo().send_mail(rec.id, force_send=True, email_values={'email_to': visitor_contact})

        # Human-readable state labels for template
        state_labels = {
            'draft': _('Draft'),
            'to_approve': _('To Approve'),
            'approved': _('Approved'),
            'issued': _('Issued'),
            'checked_out': _('Checked Out'),
            'returned': _('Returned'),
            'closed': _('Closed'),
            'rejected': _('Rejected'),
            'cancel': _('Canceled'),
        }
        return request.render('hr_gate_pass_webform.template_gate_pass_success', {
            'record': rec,
            'state_labels': state_labels,
            'state_label': state_labels.get(rec.state, rec.state),
        })

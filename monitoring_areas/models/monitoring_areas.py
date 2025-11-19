# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import base64
from io import BytesIO
import random
import string

try:
	import qrcode
except Exception:
	qrcode = None


class WorkPermitArea(models.Model):
	_name = 'work.permit.area'
	_description = 'Work Permit Area'
	_order = 'name'
	_check_company_auto = True

	name = fields.Char(required=True, index=True)
	code = fields.Char(string='Code', help='Short code for the area')
	active = fields.Boolean(default=True)
	company_id = fields.Many2one(
		'res.company',
		string='Company',
		required=True,
		default=lambda self: self.env.company,
		index=True,
	)

	_sql_constraints = [
		('name_company_unique', 'unique(name, company_id)', 'Area name must be unique per company.'),
	]


class MonitoringAreas(models.Model):
	_name = 'monitoring.areas'
	_description = 'Monitoring Areas'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_rec_name = 'area_id'
	_check_company_auto = True

	name = fields.Char(string='Reference', required=True, copy=False, index=True, default='New')
	company_id = fields.Many2one(
		'res.company',
		string='Company',
		required=True,
		default=lambda self: self.env.company,
		index=True,
		tracking=True,
	)
	area_id = fields.Many2one(
		'work.permit.area',
		string='Area',
		required=True,
		ondelete='restrict',
		tracking=True,
		check_company=True,
	)

	# QR fields: stored unique code and generated image
	qr_value = fields.Char(string='QR Code', readonly=True, copy=False, index=True)
	qr_image = fields.Binary(string='QR Image', attachment=True, compute='_compute_qr_fields', store=False)

	_sql_constraints = [
		('qr_value_unique', 'unique(qr_value)', 'QR Code must be unique.'),
		('area_unique', 'unique(area_id)', 'Only one monitoring record is allowed per Area.'),
	]

	@api.model
	def _generate_unique_code(self, length: int = 8) -> str:
		alphabet = string.ascii_uppercase + string.digits
		# Try a few times to avoid rare collisions
		for _ in range(10):
			code = ''.join(random.choices(alphabet, k=length))
			# We only ensure random code uniqueness statistically here; the final
			# uniqueness will be validated against the full composed qr_value.
			return code
		# Fallback with timestamp-based suffix if improbable collisions keep occurring
		return ''.join(random.choices(alphabet, k=length))

	def _compose_qr_value(self, area, code: str, company=None) -> str:
		"""Build the QR payload string including company and area information.

		Format: C:{company};A:{area};K:{code}
		"""
		company_rec = company or (area.company_id if area else False) or self.env.company
		company_name = company_rec.name or ''
		area_name = area.name if area else ''
		# Use separators that are easy to parse if needed
		return f"Company:{company_name},\nWork Area:{area_name}, \nUnique Code:{code}"

	@api.model_create_multi
	def create(self, vals_list):
		# Pre-validate: ensure no duplicate area in batch or existing records
		areas_in_batch = [vals.get('area_id') for vals in vals_list if vals.get('area_id')]
		# Duplicates within the same batch
		if len(set(areas_in_batch)) != len(areas_in_batch):
			raise ValidationError('You cannot create multiple monitoring records for the same Area in a single operation.')
		if areas_in_batch:
			# Existing duplicates in DB
			if self.search_count([('area_id', 'in', areas_in_batch)]) > 0:
				raise ValidationError('A monitoring record already exists for one of the selected Areas.')

		ResCompany = self.env['res.company']
		WorkArea = self.env['work.permit.area']
		for vals in vals_list:
			if vals.get('area_id'):
				area = WorkArea.browse(vals['area_id'])
				vals['company_id'] = area.company_id.id
			else:
				vals.setdefault('company_id', self.env.company.id)
			# Assign sequence at create time (prevents double consumption)
			if vals.get('name', 'New') == 'New':
				vals['name'] = self.env['ir.sequence'].next_by_code('monitoring.areas') or '/'
			# Build QR payload with company + area + random key
			if not vals.get('qr_value'):
				area = None
				company = ResCompany.browse(vals['company_id']) if vals.get('company_id') else self.env.company
				if vals.get('area_id'):
					area = WorkArea.browse(vals['area_id'])
				# generate until composed value is unique
				for _ in range(10):
					code = self._generate_unique_code()
					candidate = self._compose_qr_value(area, code, company=company)
					if not self.search_count([('qr_value', '=', candidate)]):
						vals['qr_value'] = candidate
						break
				# As a last resort if loop didn't set it (extremely unlikely)
				if not vals.get('qr_value'):
					vals['qr_value'] = self._compose_qr_value(area, self._generate_unique_code(), company=company)
		return super().create(vals_list)

	def _make_qr_image(self, value: str):
		if not value or qrcode is None:
			return False
		buf = BytesIO()
		qr = qrcode.QRCode(version=1, box_size=4, border=2)
		qr.add_data(value)
		qr.make(fit=True)
		img = qr.make_image(fill_color="black", back_color="white")
		img.save(buf, 'PNG')
		return base64.b64encode(buf.getvalue())

	@api.depends('qr_value')
	def _compute_qr_fields(self):
		for rec in self:
			rec.qr_image = self._make_qr_image(rec.qr_value)

	@api.onchange('area_id')
	def _onchange_area_regenerate_qr(self):
		for rec in self:
			if rec.area_id:
				rec.company_id = rec.area_id.company_id
				new_code = rec._generate_unique_code()
				new_value = rec._compose_qr_value(rec.area_id, new_code, company=rec.company_id)
				rec.qr_value = new_value
				rec.qr_image = rec._make_qr_image(new_value)

	def write(self, vals):
		# Pre-validate area change to avoid SQL errors and provide friendly message
		if 'area_id' in vals and vals['area_id']:
			for rec in self:
				duplicate = self.search([('area_id', '=', vals['area_id']), ('id', '!=', rec.id)], limit=1)
				if duplicate:
					raise ValidationError('A monitoring record already exists for this Area.')
			area = self.env['work.permit.area'].browse(vals['area_id'])
			vals = dict(vals)
			vals['company_id'] = area.company_id.id

		res = super().write(vals)
		if 'area_id' in vals:
			for rec in self:
				# regenerate unique code and composed value on area change
				for _ in range(10):
					new_code = rec._generate_unique_code()
					candidate = rec._compose_qr_value(rec.area_id, new_code, company=rec.company_id)
					if not self.search_count([('qr_value', '=', candidate), ('id', '!=', rec.id)]):
						super(MonitoringAreas, rec).write({'qr_value': candidate})
						break
				else:
					# fallback write
					super(MonitoringAreas, rec).write({'qr_value': rec._compose_qr_value(rec.area_id, rec._generate_unique_code(), company=rec.company_id)})
		return res

	@api.constrains('area_id', 'company_id')
	def _check_area_company(self):
		for rec in self:
			if rec.area_id and rec.area_id.company_id != rec.company_id:
				raise ValidationError(_('The monitoring area company must match the selected area.'))


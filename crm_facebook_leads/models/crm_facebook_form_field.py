from odoo import models, fields


class CrmFacebookFormField(models.Model):
    _name = 'crm.facebook.form.field'
    _description = 'Facebook form fields'

    form_id = fields.Many2one('crm.facebook.form', required=True, ondelete='cascade', string='Form')
    name = fields.Char()
    odoo_field_id = fields.Many2one(
        'ir.model.fields',
        domain=[('model', '=', 'crm.lead'), ('store', '=', True), ('ttype', 'in', (
            'char', 'date', 'datetime', 'float', 'html', 'integer', 'monetary', 'many2one', 'selection', 'phone',
            'text'))])
    facebook_field = fields.Char(required=True)

    _sql_constraints = [
        ('field_unique', 'unique(form_id, odoo_field_id, facebook_field)', 'Mapping must be unique per form')]

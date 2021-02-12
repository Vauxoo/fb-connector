import requests

from odoo import models, fields


def check_version_field(url):
    version = url.rsplit('v')[-1].rstrip('/')
    try:
        ver_num = float(version)
    except (TypeError, ValueError):
        return 'questions'
    return 'questions' if ver_num >= 5 else 'qualifiers'


class CrmFacebookForm(models.Model):
    _name = 'crm.facebook.form'
    _description = 'Facebook Form Page'

    name = fields.Char(required=True)
    allow_to_sync = fields.Boolean()
    id_facebook_form = fields.Char(string='Form ID', required=True, readonly=True)
    access_token = fields.Char(required=True, related='page_id.access_token', string='Page Access Token')
    page_id = fields.Many2one('crm.facebook.page', readonly=True, ondelete='cascade', string='Facebook Page')
    mappings = fields.One2many('crm.facebook.form.field', 'form_id')
    team_id = fields.Many2one(
        'crm.team', domain=['|', ('use_leads', '=', True), ('use_opportunities', '=', True)], string="Sales Team")
    campaign_id = fields.Many2one('utm.campaign')
    source_id = fields.Many2one('utm.source')
    medium_id = fields.Many2one('utm.medium')

    def get_fields(self):
        self.mappings.unlink()
        fb_api = self.env['ir.config_parameter'].get_param('facebook.api.url')
        vfield = check_version_field(fb_api)
        response = requests.get(
            fb_api + self.facebook_form, params={'access_token': self.access_token, 'fields': vfield}).json()
        for qualifier in response.get(vfield, []):
            self.env['crm.facebook.form.field'].create({
                'form_id': self.id,
                'name': qualifier['label'],
                'facebook_field': qualifier.get('key', False) or qualifier.get('field_key', False)
            })


class CrmFacebookFormField(models.Model):
    _name = 'crm.facebook.form.field'
    _description = 'Facebook form fields'

    form_id = fields.Many2one('crm.facebook.form', required=True, ondelete='cascade', string='Form')
    name = fields.Char()
    odoo_field = fields.Many2one(
        'ir.model.fields',
        domain=[('model', '=', 'crm.lead'), ('store', '=', True), ('ttype', 'in', (
            'char', 'date', 'datetime', 'float', 'html', 'integer', 'monetary', 'many2one', 'selection', 'phone',
            'text'))], required=False)
    facebook_field = fields.Char(required=True)

    _sql_constraints = [
        ('field_unique', 'unique(form_id, odoo_field, facebook_field)', 'Mapping must be unique per form')]

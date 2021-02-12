import requests

from odoo import models, fields


class CrmFacebookPage(models.Model):
    _name = 'crm.facebook.page'
    _description = 'Facebook Page'

    name = fields.Char(required=True)
    access_token = fields.Char(required=True, string='Page Access Token')
    form_ids = fields.One2many('crm.facebook.form', 'page_id', string='Lead Forms')

    def form_processing(self, response):
        if not response.get('data'):
            return
        for form in response['data']:
            if self.form_ids.filtered(lambda f: f.id_facebook_form == form['id']):
                continue
            self.form_ids.create({
                'name': form['name'],
                'id_facebook_form': form['id'],
                'page_id': self.id}).get_fields()

        if response.get('paging', {}).get('next'):
            self.form_processing(requests.get(response['paging']['next']).json())

    def get_forms(self):
        fb_api = self.env['ir.config_parameter'].get_param('facebook.api.url')
        response = requests.get(
            fb_api + self.name + "/leadgen_forms",
            params={'access_token': self.access_token}).json()
        self.form_processing(response)

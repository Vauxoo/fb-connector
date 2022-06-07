import logging
from urllib import parse

import requests

from odoo import api, fields, models

_logger = logging.getLogger()


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    id_facebook_lead = fields.Char(string="Facebook Lead ID", readonly=True)
    facebook_page_id = fields.Many2one(
        'crm.facebook.page', related='facebook_form_id.page_id', store=True)
    facebook_form_id = fields.Many2one('crm.facebook.form', readonly=True)
    facebook_adset_id = fields.Many2one('utm.adset', readonly=True)
    facebook_date_create = fields.Datetime(readonly=True)
    facebook_is_organic = fields.Boolean(readonly=True)

    _sql_constraints = [('facebook_lead_unique', 'unique(id_facebook_lead)', 'This Facebook lead already exists!')]

    def get_ad(self, lead):
        ad_obj = self.env['utm.medium']
        if not lead.get('ad_id'):
            return ad_obj
        fb_ad = ad_obj.search([('id_facebook_ad', '=', lead['ad_id'])], limit=1)
        if not fb_ad:
            return ad_obj.create({
                'id_facebook_ad': lead['ad_id'],
                'name': lead['ad_name'],
            }).id

        return fb_ad.id

    def get_adset(self, lead):
        ad_obj = self.env['utm.adset']
        if not lead.get('adset_id'):
            return ad_obj
        fb_adset = ad_obj.search([('id_facebook_adset', '=', lead['adset_id'])], limit=1)
        if not fb_adset:
            return ad_obj.create({'id_facebook_adset': lead['adset_id'], 'name': lead['adset_name'], }).id

        return fb_adset.id

    def get_campaign(self, lead):
        campaign_obj = self.env['utm.campaign']
        if not lead.get('campaign_id'):
            return campaign_obj
        fb_camp = campaign_obj.search([('id_facebook_campaign', '=', lead['campaign_id'])], limit=1)
        if not fb_camp:
            return campaign_obj.create({
                'id_facebook_campaign': lead['campaign_id'],
                'name': lead['campaign_name']
            }).id

        return fb_camp.id

    def _prepare_lead_creation(self, lead, form):
        vals, notes = self.get_fields_from_data(lead, form)
        if not vals.get('email_from') and lead.get('email'):
            vals['email_from'] = lead['email']
        if not vals.get('contact_name') and lead.get('full_name'):
            vals['contact_name'] = lead['full_name']
        if not vals.get('phone') and lead.get('phone_number'):
            vals['phone'] = lead['phone_number']
        vals.update({
            'id_facebook_lead': lead['id'],
            'facebook_is_organic': lead['is_organic'],
            'name': self.get_opportunity_name(vals, lead, form),
            'description': "\n".join(notes),
            'team_id': form.team_id and form.team_id.id,
            'campaign_id': form.campaign_id and form.campaign_id.id or
            self.get_campaign(lead),
            'source_id': form.source_id and form.source_id.id,
            'medium_id': form.medium_id and form.medium_id.id or
            self.get_ad(lead),
            'user_id': form.team_id and form.team_id.user_id and form.team_id.user_id.id or False,
            'facebook_adset_id': self.get_adset(lead),
            'facebook_form_id': form.id,
            'facebook_date_create': lead['created_time'].split('+')[0].replace('T', ' ')
        })
        return vals

    def lead_creation(self, lead, form):
        vals = self._prepare_lead_creation(lead, form)
        return self.create(vals)

    def get_opportunity_name(self, vals, lead, form):
        if not vals.get('name'):
            vals['name'] = '%s - %s' % (form.name, lead['id'])
        return vals['name']

    def get_fields_from_data(self, lead, form):
        vals, notes = {}, []
        form_mapping = form.mappings.filtered("odoo_field_id").mapped('facebook_field')
        unmapped_fields = []
        for name, value in lead.items():
            if name not in form_mapping:
                unmapped_fields.append((name, value))
                continue
            odoo_field = form.mappings.filtered(lambda m: m.facebook_field == name).odoo_field_id
            notes.append('%s: %s' % (odoo_field.field_description, value))
            if odoo_field.ttype == 'many2one':
                related_value = self.env[odoo_field.relation].search([('display_name', '=', value)])
                vals.update({odoo_field.name: related_value and related_value.id})
            elif odoo_field.ttype in ('float', 'monetary'):
                vals.update({odoo_field.name: float(value)})
            elif odoo_field.ttype == 'integer':
                vals.update({odoo_field.name: int(value)})
            # TODO: separate date & datetime into two different conditionals
            elif odoo_field.ttype in ('date', 'datetime'):
                vals.update({odoo_field.name: value.split('+')[0].replace('T', ' ')})
            elif odoo_field.ttype == 'selection':
                vals.update({odoo_field.name: value})
            elif odoo_field.ttype == 'boolean':
                vals.update({odoo_field.name: value == 'true' if value else False})
            else:
                vals.update({odoo_field.name: value})

        # NOTE: Doing this to put unmapped fields at the end of the description
        for name, value in unmapped_fields:
            notes.append('%s: %s' % (name, value))

        return vals, notes

    def process_lead_field_data(self, lead):
        field_data = lead.pop('field_data')
        lead_data = dict(lead)
        lead_data.update([
            (ld['name'], ld['values'][0])
            for ld in field_data
            if ld.get('name') and ld.get('values')
        ])
        return lead_data

    def lead_processing(self, response, form):
        data = response.get('data', False)
        while data:
            # /!\ NOTE: Once finished a page let us commit that
            with self.env.cr.savepoint():
                for lead in data:
                    lead = self.process_lead_field_data(lead)
                    existing_lead = self.with_context(active_test=False).search([
                        ('id_facebook_lead', '=', lead.get('id'))],
                        limit=1)
                    if not existing_lead:
                        self.lead_creation(lead, form)

            if response.get('paging', {}).get('next'):
                res = requests.get(response['paging']['next']).json()
                data = res.get('data', False)
            else:
                data = False

    @api.model
    def get_facebook_leads(self):
        fb_api = self.env['ir.config_parameter'].get_param('facebook.api.url')
        for form in self.env['crm.facebook.form'].search([('allow_to_sync', '=', True)]):
            # /!\ NOTE: We have to try lead creation if it fails we just log it into the Lead Form?
            _logger.info('Starting to fetch leads from Form: %s', form.name)
            var = fb_api + form.id_facebook_form + "/leads"
            params = {
                'access_token': form.access_token,
                'fields':
                    'created_time,field_data,ad_id,ad_name,adset_id,adset_name,campaign_id,campaign_name,is_organic',
                'filtering': [{
                    "field": "time_created",
                    "operator": "GREATER_THAN",
                    "value": 1537920000,
                }],
            }
            response = requests.get(var, params=parse.urlencode(params)).json()
            self.lead_processing(response, form)
        _logger.info('Fetch of leads has ended')

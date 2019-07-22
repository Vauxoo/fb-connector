# -*- coding: utf-8 -*-

import logging
import requests

from odoo import models, fields, api


_logger = logging.getLogger(__name__)


class CrmFacebookPage(models.Model):
    _name = 'crm.facebook.page'
    _description = 'Facebook Page'

    name = fields.Char(required=True)
    access_token = fields.Char(required=True, string='Page Access Token')
    form_ids = fields.One2many('crm.facebook.form', 'page_id', string='Lead Forms')

    def form_processing(self, r):
        if not r.get('data'):
            return

        for form in r['data']:
            if self.form_ids.filtered(
                    lambda f: f.facebook_form_id == form['id']):
                continue
            self.env['crm.facebook.form'].create({
                'name': form['name'],
                'facebook_form_id': form['id'],
                'page_id': self.id}).get_fields()

        if r.get('paging') and r['paging'].get('next'):
            self.form_processing(requests.get(r['paging']['next']).json())
        return

    @api.multi
    def get_forms(self):
        r = requests.get("https://graph.facebook.com/v2.12/" + self.name + "/leadgen_forms", params = {'access_token': self.access_token}).json()
        self.form_processing(r)

class CrmFacebookForm(models.Model):
    _name = 'crm.facebook.form'
    _description = 'Facebook Form Page'

    name = fields.Char(required=True)
    allow_to_sync = fields.Boolean()
    facebook_form_id = fields.Char(required=True, string='Form ID')
    access_token = fields.Char(required=True, related='page_id.access_token', string='Page Access Token')
    page_id = fields.Many2one('crm.facebook.page', readonly=True, ondelete='cascade', string='Facebook Page')
    mappings = fields.One2many('crm.facebook.form.field', 'form_id')
    team_id = fields.Many2one('crm.team', domain=['|', ('use_leads', '=', True), ('use_opportunities', '=', True)], string="Sales Team")
    campaign_id = fields.Many2one('utm.campaign')
    source_id = fields.Many2one('utm.source')
    medium_id = fields.Many2one('utm.medium')

    def get_fields(self):
        self.mappings.unlink()
        r = requests.get("https://graph.facebook.com/v2.12/" + self.facebook_form_id, params = {'access_token': self.access_token, 'fields': 'qualifiers'}).json()
        if r.get('qualifiers'):
            for qualifier in r.get('qualifiers'):
                self.env['crm.facebook.form.field'].create({
                                                                'form_id': self.id,
                                                                'name': qualifier['label'],
                                                                'facebook_field': qualifier['field_key']
                                                            })

class CrmFacebookFormField(models.Model):
    _name = 'crm.facebook.form.field'
    _description = 'Facebook form fields'

    form_id = fields.Many2one('crm.facebook.form', required=True, ondelete='cascade', string='Form')
    name = fields.Char()
    odoo_field = fields.Many2one('ir.model.fields',
                                 domain=[('model', '=', 'crm.lead'),
                                         ('store', '=', True),
                                         ('ttype', 'in', ('char',
                                                          'date',
                                                          'datetime',
                                                          'float',
                                                          'html',
                                                          'integer',
                                                          'monetary',
                                                          'many2one',
                                                          'selection',
                                                          'phone',
                                                          'text'))],
                                 required=False)
    facebook_field = fields.Char(required=True)

    _sql_constraints = [
                        ('field_unique', 'unique(form_id, odoo_field, facebook_field)', 'Mapping must be unique per form')
    ]


class UtmMedium(models.Model):
    _inherit = 'utm.medium'

    facebook_ad_id = fields.Char()

    _sql_constraints = [
        ('facebook_ad_unique', 'unique(facebook_ad_id)',
         'This Facebook Ad already exists!')
    ]


class UtmAdset(models.Model):
    _name = 'utm.adset'
    _description = 'Utm Adset'

    name = fields.Char()
    facebook_adset_id = fields.Char()

    _sql_constraints = [
        ('facebook_adset_unique', 'unique(facebook_adset_id)',
         'This Facebook AdSet already exists!')
    ]


class UtmCampaign(models.Model):
    _inherit = 'utm.campaign'

    facebook_campaign_id = fields.Char()

    _sql_constraints = [
        ('facebook_campaign_unique', 'unique(facebook_campaign_id)',
         'This Facebook Campaign already exists!')
    ]


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    facebook_lead_id = fields.Char(readonly=True)
    facebook_page_id = fields.Many2one(
        'crm.facebook.page', related='facebook_form_id.page_id',
        store=True, readonly=True)
    facebook_form_id = fields.Many2one('crm.facebook.form', readonly=True)
    facebook_adset_id = fields.Many2one('utm.adset', readonly=True)
    facebook_ad_id = fields.Many2one(
        'utm.medium', related='medium_id', store=True, readonly=True,
        string='Facebook Ad')
    facebook_campaign_id = fields.Many2one(
        'utm.campaign', related='campaign_id', store=True, readonly=True,
        string='Facebook Campaign')
    facebook_date_create = fields.Datetime(readonly=True)
    facebook_is_organic = fields.Boolean(readonly=True)

    _sql_constraints = [
        ('facebook_lead_unique', 'unique(facebook_lead_id)',
         'This Facebook lead already exists!')
    ]

    def get_ad(self, lead):
        ad_obj = self.env['utm.medium']
        if not lead.get('ad_id'):
            return ad_obj
        if not ad_obj.search(
                [('facebook_ad_id', '=', lead['ad_id'])]):
            return ad_obj.create({
                'facebook_ad_id': lead['ad_id'], 'name': lead['ad_name'], }).id

        return ad_obj.search(
            [('facebook_ad_id', '=', lead['ad_id'])], limit=1)[0].id

    def get_adset(self, lead):
        ad_obj = self.env['utm.adset']
        if not lead.get('adset_id'):
            return ad_obj
        if not ad_obj.search(
                [('facebook_adset_id', '=', lead['adset_id'])]):
            return ad_obj.create({
                'facebook_adset_id': lead['adset_id'], 'name': lead['adset_name'], }).id

        return ad_obj.search(
            [('facebook_adset_id', '=', lead['adset_id'])], limit=1)[0].id

    def get_campaign(self, lead):
        campaign_obj = self.env['utm.campaign']
        if not lead.get('campaign_id'):
            return campaign_obj
        if not campaign_obj.search(
                [('facebook_campaign_id', '=', lead['campaign_id'])]):
            return campaign_obj.create({
                'facebook_campaign_id': lead['campaign_id'],
                'name': lead['campaign_name'], }).id

        return campaign_obj.search(
            [('facebook_campaign_id', '=', lead['campaign_id'])],
            limit=1)[0].id

    def prepare_lead_creation(self, lead, form):
        vals, notes = self.get_fields_from_data(lead, form)
        if not vals.get('email_from') and lead.get('email'):
            vals['email_from'] = lead['email']
        if not vals.get('contact_name') and lead.get('full_name'):
            vals['contact_name'] = lead['full_name']
        if not vals.get('phone') and lead.get('phone_number'):
            vals['phone'] = lead['phone_number']
        vals.update({
            'facebook_lead_id': lead['id'],
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
        vals = self.prepare_lead_creation(lead, form)
        return self.create(vals)

    def get_opportunity_name(self, vals, lead, form):
        if not vals.get('name'):
            vals['name'] = '%s - %s' % (form.name, lead['id'])
        return vals['name']

    def get_fields_from_data(self, lead, form):
        vals, notes = {}, []
        form_mapping = form.mappings.filtered(lambda m: m.odoo_field).mapped('facebook_field')
        unmapped_fields = []
        for name, value in lead.items():
            if name not in form_mapping:
                unmapped_fields.append((name, value))
                continue
            odoo_field = form.mappings.filtered(lambda m: m.facebook_field == name).odoo_field
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
        lead_data.update([(l['name'], l['values'][0])
                          for l in field_data
                          if l.get('name') and l.get('values')])
        return lead_data

    def lead_processing(self, r, form):
        if not r.get('data'):
            return
        for lead in r['data']:
            lead = self.process_lead_field_data(lead)
            if not self.search([('facebook_lead_id', '=', lead.get('id')), '|', ('active', '=', True), ('active', '=', False)]):
                self.lead_creation(lead, form)

        # /!\ NOTE: Once finished a page let us commit that
        try:
            self.env.cr.commit()
        except Exception:
            self.env.cr.rollback()

        if r.get('paging') and r['paging'].get('next'):
            _logger.info('Fetching a new page in Form: %s' % form.name)
            self.lead_processing(requests.get(r['paging']['next']).json(), form)
        return

    @api.model
    def get_facebook_leads(self):
        # /!\ TODO: Add this URL as a configuration setting in the company
        fb_api = "https://graph.facebook.com/v2.12/"
        for form in self.env['crm.facebook.form'].search([('allow_to_sync', '=', True)]):
            # /!\ NOTE: We have to try lead creation if it fails we just log it into the Lead Form?
            _logger.info('Starting to fetch leads from Form: %s' % form.name)
            r = requests.get(fb_api + form.facebook_form_id + "/leads", params = {'access_token': form.access_token, 'fields': 'created_time,field_data,ad_id,ad_name,adset_id,adset_name,campaign_id,campaign_name,is_organic'}).json()
            self.lead_processing(r, form)
        _logger.info('Fetch of leads has ended')

from odoo import fields, models


class UtmCampaign(models.Model):
    _inherit = 'utm.campaign'

    id_facebook_campaign = fields.Char(string="Facebook Campaign ID")

    _sql_constraints = [
        ('facebook_campaign_unique', 'unique(id_facebook_campaign)', 'This Facebook Campaign already exists!')
    ]

from odoo import fields, models


class UtmMedium(models.Model):
    _inherit = 'utm.medium'

    id_facebook_ad = fields.Char(string="Facebook Ad ID")

    _sql_constraints = [('facebook_ad_unique', 'unique(id_facebook_ad)', 'This Facebook Ad already exists!')]

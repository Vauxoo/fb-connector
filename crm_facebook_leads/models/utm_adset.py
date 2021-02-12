from odoo import fields, models


class UtmAdset(models.Model):
    _name = 'utm.adset'
    _description = 'Utm Adset'

    name = fields.Char()
    id_facebook_adset = fields.Char(string="Adset ID")

    _sql_constraints = [('facebook_adset_unique', 'unique(id_facebook_adset)', 'This Facebook AdSet already exists!')]

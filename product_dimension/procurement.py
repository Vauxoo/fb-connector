# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2015 BADEP. All Rights Reserved.
#    Author: Khalid Hazam<k.hazam@badep.ma>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp

class procurement_order(models.Model):
    _inherit = "procurement.order"
    dimensions = fields.One2many('procurement.order.dimension','procurement_order')
    
    @api.model
    def _prepare_mo_vals(self, procurement):
        res = super(procurement, self)._prepare_mo_vals(procurement)
        res['dimensions'] = [(0, 0, {'dimension': x.dimension.id, 'quantity': x.quantity}) for x in procurement.dimensions]
        return res
procurement_order()

class procurement_order_dimension(models.Model):
    _name = "procurement.order.dimension"
    dimension = fields.Many2one('product.uom.dimension', required=True, ondelete='cascade')
    quantity = fields.Float('Quantity', digits_compute= dp.get_precision('Product UoS'), required=True)
    procurement_order = fields.Many2one('procurement.order','Procurement Order', required=True, ondelete='cascade')

procurement_order_dimension()
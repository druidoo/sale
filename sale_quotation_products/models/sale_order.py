##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api, _
from ast import literal_eval


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def add_products_to_quotation(self):
        self.ensure_one()
        action = self.env.ref('product.product_normal_action_sell').read()[0]
        context = literal_eval(action['context'])
        context.update({
            'sale_quotation_products': True,
            'pricelist': self.pricelist_id.display_name,
            # we send company in context so it filters taxes
            'company_id': self.company_id.id,
            'partner_id': self.partner_id.id,
            'search_default_location_id': self.warehouse_id.lot_stock_id.id,
        })
        action.update({
            'context': context,
            'name': _('Quotation Products'),
        })
        return action

    @api.multi
    def add_products(self, product_ids, qty):
        self.ensure_one()
        sol = self.env['sale.order.line']
        for product in self.env['product.product'].browse(product_ids):
            last_sol = sol.search(
                [('order_id', '=', self.id)], order='sequence desc', limit=1)
            sequence = last_sol and last_sol.sequence + 1 or 10
            vals = {
                'order_id': self.id,
                'product_id': product.id or False,
                'sequence': sequence,
                'company_id': self.company_id.id,
            }
            sol = sol.new(vals)
            sol.product_id_change()
            sol.product_uom_qty = qty
            sol.product_uom_change()
            sol._onchange_discount()
            vals = sol._convert_to_write(sol._cache)
            sol.create(vals)

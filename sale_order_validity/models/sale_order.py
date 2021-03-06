from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class SaleOrder(models.Model):

    _inherit = "sale.order"

    validity_days = fields.Integer(
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        help='Set days of validity for Sales Order',
    )

    validity_date = fields.Date(
        help="Date until when quotation is valid",
        readonly=True,
        track_visibility='onchange',
    )

    date_order = fields.Datetime(
        copy=True,
    )

    @api.onchange('date_order', 'validity_days')
    @api.constrains('date_order', 'validity_days')
    def get_validity_date(self):
        for rec in self.filtered(lambda x: x.validity_days):
            date_order = fields.Datetime.from_string(rec.date_order)
            rec.validity_date = fields.Datetime.to_string(
                date_order + relativedelta(days=rec.validity_days))

    @api.onchange('company_id')
    @api.constrains('company_id')
    def onchange_company(self):
        for rec in self:
            rec.validity_days = rec.company_id.sale_order_validity_days

    @api.onchange('validity_days')
    def onchange_validity_days(self):
        company_validity_days = self.company_id.sale_order_validity_days
        if self.validity_days > company_validity_days:
            self.validity_days = self.company_id.sale_order_validity_days
            warning = {
                'title': _('Warning!'),
                'message': _(
                    'You can not set more validity days than the configured on'
                    ' the company (%i days).' % company_validity_days),
            }
            return {'warning': warning}

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        self.check_validity()
        return super(SaleOrder, self).action_confirm()

    @api.multi
    def check_validity(self):
        if self.validity_date:
            validity_date = fields.Datetime.from_string(self.validity_date)
            now = fields.Datetime.from_string(fields.Datetime.now())
            if validity_date < now:
                raise UserError(_(
                    'You can not confirm this quoatation as it was valid until'
                    ' %s! Please Update Validity.') % (self.validity_date))

    @api.multi
    def update_date_prices_and_validity(self):
        self.date_order = fields.Datetime.now()
        self.update_prices()
        self.onchange_company()
        return True

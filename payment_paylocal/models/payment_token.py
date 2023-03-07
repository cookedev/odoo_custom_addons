from odoo import fields, models
from odoo.exceptions import UserError


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    paylocal_customer_id = fields.Char("Customer ID", help="The unique reference of the partner owning this token", readonly=True)

    def _handle_deactivation_request(self):
        """
        Request PayLocal to deactivate this payment token

        :return: None
        """

        super()._handle_deactivation_request()
        if self.provider != 'paylocal':
            return

        data = {}  # TODO: How to manage PayLocal tokens? Disable Authorized transaction?
        self.acquirer_id._paylocal_make_request(
            endpoint='/api/v1/',
            payload=data,
            method='POST'
        )

    def _handle_reactivation_request(self):
        """
        Request PayLocal to reactivate this payment token

        :return: None
        :raise: UserError if the token is managed by PayLocal  TODO: How to manage PayLocal tokens? Disable Authorized transaction? Can they be reactivated?
        """
        super()._handle_reactivation_request()
        if self.provider != 'paylocal':
            return

        raise UserError("Saved payment methods cannot be restored once they have been deactivated.")

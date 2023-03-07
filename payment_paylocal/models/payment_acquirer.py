from odoo import fields, models
from odoo.exceptions import ValidationError
from datetime import timedelta
import logging
import requests

_logger = logging.getLogger(__name__)
PAYLOCAL_REQUEST_TIMEOUT = 30


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('paylocal', "PayLocal")], ondelete={'paylocal': 'set default'})
    paylocal_api_url = fields.Char(string="Paylocal URL", help="The base URL for the API endpoints", required_if_provider='paylocal')
    paylocal_api_user = fields.Char(string="Username", help="The Paylocal webservice username", required_if_provider='paylocal', groups='base.group_system')
    paylocal_api_pass = fields.Char(string="Password", help="The Paylocal webservice password", required_if_provider='paylocal', groups='base.group_system')
    paylocal_merchant_gateway = fields.Char(string="Merchant Gateway", required_if_provider='paylocal', groups='base.group_system')
    paylocal_jwt_token = fields.Char(readonly=True, groups='base.group_system')
    paylocal_jwt_token_expiration = fields.Datetime(readonly=True, groups='base.group_system')

    def _ensure_paylocal_acquirer(self):
        self.ensure_one()
        if not self.provider == 'paylocal':
            _logger.exception("invalid Acquirer: Expected 'paylocal', got %s", self.provider)
            raise ValidationError("Acquirer error: PayLocal")

    def _paylocal_ensure_authenticated(self, force_refresh=False):
        self._ensure_paylocal_acquirer()

        if force_refresh or not self.paylocal_jwt_token_expiration or fields.Datetime.now() > self.paylocal_jwt_token_expiration:
            _logger.info('Refreshing Paylocal token. Forced=%s', force_refresh)
            url = f"{self.paylocal_api_url.rstrip('/')}/oauth/token"
            headers = {'Content-Type': 'application/json'}
            data = {
                'grant_type': "password",
                'username': self.paylocal_api_user,
                'password': self.paylocal_api_pass,
                'client_id': "paylocal"
            }
            r = requests.request('POST', url, json=data, headers=headers, timeout=PAYLOCAL_REQUEST_TIMEOUT)
            res = r.json()

            new_token = res.get('access_token')
            if res.get('error') or not new_token:
                _logger.error("Could not authenticate Paylocal: %s", str(res))
                raise ValidationError("PayLocal: Could not authenticate with the API")
            r.raise_for_status()

            expires_in = res.get('expires_in', 600)
            self.paylocal_jwt_token = new_token
            self.paylocal_jwt_token_expiration = fields.Datetime.now() + timedelta(seconds=expires_in)

    def _paylocal_make_request(self, endpoint: str, payload: dict = None, method='POST'):
        """
        :return: The JSON-formatted dict content of the response
        :raise: ValidationError if an HTTP error occurs
        """

        self._ensure_paylocal_acquirer()

        url = f"{self.paylocal_api_url.rstrip('/')}/{endpoint.lstrip('/')}"

        try:
            self._paylocal_ensure_authenticated()
            headers = {'content-type': 'application/json', 'Authorization': self.paylocal_jwt_token}
            response = requests.request(method, url, json=payload, headers=headers, timeout=PAYLOCAL_REQUEST_TIMEOUT)
            if response.json().get('error') == 'access_denied':
                self._paylocal_ensure_authenticated(force_refresh=True)
                headers = {'content-type': 'application/json', 'Authorization': self.paylocal_jwt_token}
                response = requests.request(method, url, data=payload, headers=headers, timeout=PAYLOCAL_REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            _logger.exception("unable to reach endpoint at %s", url)
            raise ValidationError("Could not establish a connection to PayLocal")
        except requests.exceptions.HTTPError as error:
            _logger.exception("invalid API request at %s with data %s: %s", url, payload, error.response.text)
            raise ValidationError("The communication with PayLocal failed")
        return response.json()

    def paylocal_get_merchant_config(self):
        return self._paylocal_make_request(f'/merchant-gateway/{self.paylocal_merchant_gateway}', method='GET')

    def paylocal_get_client_jwt_token(self):
        self._ensure_paylocal_acquirer()
        data = self._paylocal_make_request('/gateway-call/get-client-token', method='POST')
        token = data.get('token', '')
        return token

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != 'paylocal':
            return super()._get_default_payment_method_id()
        return self.env.ref('payment_paylocal.payment_method_paylocal').id

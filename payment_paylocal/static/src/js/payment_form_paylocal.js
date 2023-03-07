/* global Accept */
odoo.define('payment_paylocal.payment_form', require => {
    'use strict';

    const core = require('web.core');

    const checkoutForm = require('payment.checkout_form');
    const manageForm = require('payment.manage_form');
    const paylocalClient = require('payment_paylocal.paylocal_client');

    const _t = core._t;

    const paylocalMixin = {

        /**
         * Return all relevant inline form inputs based on the payment method type of the acquirer.
         *
         * @private
         * @param {number} acquirerId - The id of the selected acquirer
         * @return {Object} - An object mapping the name of inline form inputs to their DOM element
         */
        _getInlineFormInputs: function (acquirerId) {
            return {
                name: document.getElementById(`o_paylocal_name_${acquirerId}`),
                card: document.getElementById(`o_paylocal_card_${acquirerId}`),
                month: document.getElementById(`o_paylocal_month_${acquirerId}`),
                year: document.getElementById(`o_paylocal_year_${acquirerId}`),
                // code: document.getElementById(`o_paylocal_code_${acquirerId}`),
            };
        },

        /**
         * Return the credit card or bank data to pass to tokenization request.
         *
         * @private
         * @param {number} acquirerId - The id of the selected acquirer
         * @return {Object} - Data to pass to the tokenization request
         */
        _getPaymentDetailsForTokenization: function (acquirerId) {
            const inputs = this._getInlineFormInputs(acquirerId);
            return {
                cardNumber: inputs.card.value.replaceAll(' ', '').replaceAll('-', ''), // Remove separators
                cardExpMonth: inputs.month.value,
                cardExpYear: inputs.year.value,
                cardName: inputs.month.value
                //cardCode:
            };
        },

        /**
         * Prepare the inline form of PayLocal for direct payment.
         *
         * @override method from payment.payment_form_mixin
         * @private
         * @param {string} provider - The provider of the selected payment option's acquirer
         * @param {number} paymentOptionId - The id of the selected payment option
         * @param {string} flow - The online payment flow of the selected payment option
         * @return {Promise}
         */
        _prepareInlineForm: function (provider, paymentOptionId, flow) {
            if (provider !== 'paylocal') {
                return this._super(...arguments);
            }

            if (flow === 'token') {
                return Promise.resolve(); // Don't show the form for tokens
            }

            this._hideCardForm(paymentOptionId, true);

            return this._rpc({
                route: '/payment/paylocal/get_acquirer_info',
                params: {'acquirer_id': paymentOptionId},
            }).then(acquirerInfo => {
                this.paylocalInfo = acquirerInfo;

                if(this._getPaylocalCardInputMethod() === 'lightbox') {
                    this._hideCardForm(paymentOptionId, true);
                } else {
                    this._hideCardForm(paymentOptionId, false);
                }
            }).guardedCatch((error) => {
                error.event.preventDefault();
                this._displayError(
                    _t("Server Error"),
                    _t("An error occurred when displaying this payment form."),
                    error.message.data.message
                );
            });
        },

        /**
         * Dispatch the secure data to PayLocal.
         *
         * @override method from payment.payment_form_mixin
         * @private
         * @param {string} provider - The provider of the payment option's acquirer
         * @param {number} paymentOptionId - The id of the payment option handling the transaction
         * @param {string} flow - The online payment flow of the transaction
         * @return {Promise}
         */
        _processPayment: function (provider, paymentOptionId, flow) {
            if (provider !== 'paylocal' || flow === 'token') {
                return this._super(...arguments); // Tokens are handled by the generic flow
            }

            if (!this._validateFormInputs(paymentOptionId)) {
                this._enableButton(); // The submit button is disabled at this point, enable it
                return Promise.resolve();
            }

            // Build the card data objects and dispatch to PayLocal
            const paymentDetails = this._getPaymentDetailsForTokenization(paymentOptionId);
            const self = this;

            return paylocalClient.createHeadlessClient(this.paylocalInfo.headlessClientConfig).then(
                client => client.tokenize(paymentDetails).then(
                    paymentMethod => self._responseHandler(paymentOptionId, paymentMethod)
                )
            ).catch((error) => {
                console.error(error);
                this._enableButton(); // The submit button is disabled at this point, enable it
                this._displayError(
                    _t("Error"),
                    _t("We are not able to process your payment."),
                    error.message
                );
            });
        },

        /**
         * Handle the response from PayLocal and initiate the payment.
         *
         * @private
         * @param {number} acquirerId - The id of the selected acquirer
         * @param {object} response - The payment nonce returned by PayLocal
         * @return {Promise}
         */
        _responseHandler: function (acquirerId, response) {

            // Create the transaction and retrieve the processing values
            return this._rpc({
                route: this.txContext.transactionRoute,
                params: this._prepareTransactionRouteParams('paylocal', acquirerId, 'direct'),
            }).then(processingValues => {
                // Initiate the payment
                return this._rpc({
                    route: '/payment/paylocal/payment',
                    params: {
                        'reference': processingValues.reference,
                        'partner_id': processingValues.partner_id,
                        'access_token': processingValues.access_token,
                        'paylocal_data': response,
                        'masked_data': response.cardNumberMask
                    }
                }).then(() => window.location = '/payment/status');
            }).guardedCatch((error) => {
                error.event.preventDefault();
                this._displayError(
                    _t("Server Error"),
                    _t("We are not able to process your payment."),
                    error.message.data.message
                );
            });
        },

        /**
         * Checks that all payment inputs adhere to the DOM validation constraints.
         *
         * @private
         * @param {number} acquirerId - The id of the selected acquirer
         * @return {boolean} - Whether all elements pass the validation constraints
         */
        _validateFormInputs: function (acquirerId) {

            if(this._getPaylocalCardInputMethod() === 'lightbox') {
                return true;
            }

            const inputs = Object.values(this._getInlineFormInputs(acquirerId));
            return inputs.every(element => element.reportValidity());
        },

        /**
         * Checks the gateway config for the input method.
         *
         * @private
         * @return {'form' | 'lightbox'} - Card input method
         */
        _getPaylocalCardInputMethod: function() {
            if(!this.paylocalInfo
                || !this.paylocalInfo.headlessClientConfig
                || !this.paylocalInfo.headlessClientConfig.config
                || !this.paylocalInfo.headlessClientConfig.config.inputMode
            ) {
                return 'form';
            }
 
            const inputMode = this.paylocalInfo.headlessClientConfig.config.inputMode;

            if(inputMode === 'lightbox' ) {
                return 'lightbox';
            } else {
                return 'form';
            }
        },

        /**
         * Hide or show that card information form
         *
         * @private
         * @param {number} acquirerId - The id of the selected acquirer
         * @param {boolean} hide - Will hide if true
         * @return {void}
         */
        _hideCardForm: function (acquirerId, hide) {
            const form = document.getElementById(`o_paylocal_form_${acquirerId}`);
            if(!form) {
                return;
            }

            form.style.display =  hide ? 'none' : '';
        }

    };

    checkoutForm.include(paylocalMixin);
    manageForm.include(paylocalMixin);
});

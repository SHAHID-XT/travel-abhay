import stripe
import logging
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from bookings.models import Booking, Payment

logger = logging.getLogger('tripio')

class PaymentService:
    """
    Service for handling payment operations with different payment gateways.
    """
    @staticmethod
    def initialize_stripe():
        """
        Initialize the Stripe API with the secret key.
        """
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    @staticmethod
    def create_stripe_payment_intent(booking):
        """
        Create a payment intent with Stripe for a booking.
        """
        try:
            PaymentService.initialize_stripe()
            
            # Create a payment intent
            amount_in_cents = int(booking.total_price * 100)  # Convert to cents
            intent = stripe.PaymentIntent.create(
                amount=amount_in_cents,
                currency=booking.currency.lower(),
                metadata={
                    'booking_id': str(booking.id),
                    'reference_id': booking.reference_id,
                    'user_id': str(booking.user.id),
                },
                description=f"Payment for booking {booking.reference_id}",
            )
            
            # Create a payment record
            payment = Payment.objects.create(
                booking=booking,
                amount=booking.total_price,
                currency=booking.currency,
                payment_method=Payment.PAYMENT_METHOD_CREDIT_CARD,
                payment_status=Payment.PAYMENT_STATUS_PENDING,
                transaction_id=intent.id,
                payment_gateway_response={
                    'id': intent.id,
                    'client_secret': intent.client_secret,
                },
            )
            
            return {
                'client_secret': intent.client_secret,
                'payment_id': str(payment.id),
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {
                'error': str(e),
            }
        except Exception as e:
            logger.error(f"Payment error: {str(e)}")
            return {
                'error': 'An unexpected error occurred',
            }
    
    @staticmethod
    def handle_stripe_webhook_event(event_json):
        """
        Handle Stripe webhook events to update payment status.
        """
        try:
            PaymentService.initialize_stripe()
            event_type = event_json['type']
            event_object = event_json['data']['object']
            
            # Handle payment intent succeeded
            if event_type == 'payment_intent.succeeded':
                payment_intent_id = event_object['id']
                return PaymentService.process_successful_payment(payment_intent_id)
            
            # Handle payment intent failed
            elif event_type == 'payment_intent.payment_failed':
                payment_intent_id = event_object['id']
                return PaymentService.process_failed_payment(payment_intent_id)
            
            return {'status': 'ignored', 'message': f'Event {event_type} not handled'}
            
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def process_successful_payment(payment_intent_id):
        """
        Process a successful payment by updating the payment and booking status.
        """
        try:
            # Find the payment with this transaction ID
            payment = Payment.objects.get(transaction_id=payment_intent_id)
            
            # Update payment status
            payment.payment_status = Payment.PAYMENT_STATUS_COMPLETED
            payment.save()
            
            # Update booking status
            booking = payment.booking
            booking.status = Booking.STATUS_PAID
            booking.paid_at = timezone.now()
            booking.save()
            
            return {
                'status': 'success',
                'payment_id': str(payment.id),
                'booking_id': str(booking.id),
            }
            
        except Payment.DoesNotExist:
            logger.error(f"Payment with transaction ID {payment_intent_id} not found")
            return {'status': 'error', 'message': 'Payment not found'}
        except Exception as e:
            logger.error(f"Error processing successful payment: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def process_failed_payment(payment_intent_id):
        """
        Process a failed payment by updating the payment status.
        """
        try:
            # Find the payment with this transaction ID
            payment = Payment.objects.get(transaction_id=payment_intent_id)
            
            # Update payment status
            payment.payment_status = Payment.PAYMENT_STATUS_FAILED
            payment.save()
            
            return {
                'status': 'failed',
                'payment_id': str(payment.id),
                'booking_id': str(payment.booking.id),
            }
            
        except Payment.DoesNotExist:
            logger.error(f"Payment with transaction ID {payment_intent_id} not found")
            return {'status': 'error', 'message': 'Payment not found'}
        except Exception as e:
            logger.error(f"Error processing failed payment: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    def process_refund(payment_id, amount=None, reason=None):
        """
        Process a refund for a payment.
        """
        try:
            payment = Payment.objects.get(id=payment_id)
            
            if payment.payment_status != Payment.PAYMENT_STATUS_COMPLETED:
                return {'status': 'error', 'message': 'Only completed payments can be refunded'}
            
            PaymentService.initialize_stripe()
            
            # If no amount is specified, refund the full amount
            refund_amount = amount if amount is not None else payment.amount
            refund_amount_cents = int(refund_amount * 100)
            
            # Create the refund in Stripe
            refund = stripe.Refund.create(
                payment_intent=payment.transaction_id,
                amount=refund_amount_cents,
                reason=reason or 'requested_by_customer',
            )
            
            # Update payment status
            payment.payment_status = Payment.PAYMENT_STATUS_REFUNDED
            payment.payment_gateway_response = {
                **payment.payment_gateway_response,
                'refund': {
                    'id': refund.id,
                    'amount': refund.amount,
                    'status': refund.status,
                },
            }
            payment.save()
            
            # Update booking status
            booking = payment.booking
            booking.status = Booking.STATUS_REFUNDED
            booking.save()
            
            return {
                'status': 'success',
                'refund_id': refund.id,
                'payment_id': str(payment.id),
                'booking_id': str(booking.id),
            }
            
        except Payment.DoesNotExist:
            return {'status': 'error', 'message': 'Payment not found'}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe refund error: {str(e)}")
            return {'status': 'error', 'message': str(e)}
        except Exception as e:
            logger.error(f"Refund processing error: {str(e)}")
            return {'status': 'error', 'message': str(e)}
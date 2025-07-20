"""
NOWPayments API integration service for cryptocurrency payments.
"""
import asyncio
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

import httpx
from loguru import logger

from config.settings import get_settings
from database.models import Payment, PaymentStatus, Order

settings = get_settings()


class NOWPaymentsService:
    """Service for handling NOWPayments cryptocurrency transactions."""
    
    def __init__(self):
        self.api_key = settings.nowpayments_api_key
        self.ipn_secret = settings.nowpayments_ipn_secret
        self.base_url = settings.nowpayments_base_url
        self.timeout = 30
        
    async def get_available_currencies(self) -> List[str]:
        """Get list of available cryptocurrencies."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/currencies",
                    headers=self._get_headers(),
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                return data.get("currencies", [])
        except Exception as e:
            logger.error(f"Failed to get available currencies: {e}")
            return []
    
    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get exchange rate between two currencies."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/exchange-amount/{from_currency}_{to_currency}",
                    headers=self._get_headers(),
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                return float(data.get("exchange_rate", 0))
        except Exception as e:
            logger.error(f"Failed to get exchange rate {from_currency} to {to_currency}: {e}")
            return None
    
    async def create_payment(
        self,
        order: Order,
        pay_currency: str = "btc",
        order_description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new payment request."""
        try:
            purchase_id = f"order_{order.id}_{uuid.uuid4().hex[:8]}"
            
            payment_data = {
                "price_amount": float(order.total_amount),
                "price_currency": order.currency.lower(),
                "pay_currency": pay_currency.lower(),
                "purchase_id": purchase_id,
                "order_id": order.order_number,
                "order_description": order_description or f"Order {order.order_number}",
                "success_url": f"{settings.webhook_url}/payment-success",
                "cancel_url": f"{settings.webhook_url}/payment-cancel",
                "ipn_callback_url": f"{settings.webhook_url}/payment-ipn",
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/v1/payment",
                    headers=self._get_headers(),
                    json=payment_data,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Created payment for order {order.order_number}: {data.get('payment_id')}")
                return data
                
        except Exception as e:
            logger.error(f"Failed to create payment for order {order.order_number}: {e}")
            return None
    
    async def get_payment_status(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Get payment status by payment ID."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/payment/{payment_id}",
                    headers=self._get_headers(),
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                return data
        except Exception as e:
            logger.error(f"Failed to get payment status for {payment_id}: {e}")
            return None
    
    async def get_minimum_payment_amount(self, currency: str) -> Optional[float]:
        """Get minimum payment amount for a currency."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/min-amount",
                    headers=self._get_headers(),
                    params={"currency_from": "usd", "currency_to": currency.lower()},
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                return float(data.get("min_amount", 0))
        except Exception as e:
            logger.error(f"Failed to get minimum amount for {currency}: {e}")
            return None
    
    async def verify_ipn_signature(self, payload: str, signature: str) -> bool:
        """Verify IPN signature for security."""
        try:
            expected_signature = hmac.new(
                self.ipn_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Failed to verify IPN signature: {e}")
            return False
    
    def map_payment_status(self, nowpayments_status: str) -> PaymentStatus:
        """Map NOWPayments status to our internal status."""
        status_mapping = {
            "waiting": PaymentStatus.WAITING,
            "confirming": PaymentStatus.CONFIRMING,
            "confirmed": PaymentStatus.CONFIRMED,
            "sending": PaymentStatus.SENDING,
            "partially_paid": PaymentStatus.PARTIALLY_PAID,
            "finished": PaymentStatus.FINISHED,
            "failed": PaymentStatus.FAILED,
            "refunded": PaymentStatus.REFUNDED,
            "expired": PaymentStatus.EXPIRED,
        }
        return status_mapping.get(nowpayments_status.lower(), PaymentStatus.PENDING)
    
    async def process_ipn_callback(self, ipn_data: Dict[str, Any]) -> bool:
        """Process incoming IPN callback from NOWPayments."""
        try:
            payment_id = ipn_data.get("payment_id")
            payment_status = ipn_data.get("payment_status")
            
            if not payment_id or not payment_status:
                logger.warning("Invalid IPN data received")
                return False
            
            # Update payment status in database
            from database.database import SessionLocal
            
            db = SessionLocal()
            try:
                payment = db.query(Payment).filter(
                    Payment.payment_id == payment_id
                ).first()
                
                if not payment:
                    logger.warning(f"Payment not found for IPN: {payment_id}")
                    return False
                
                old_status = payment.payment_status
                new_status = self.map_payment_status(payment_status)
                
                # Update payment details
                payment.payment_status = new_status
                payment.actually_paid = float(ipn_data.get("actually_paid", 0))
                payment.actually_paid_currency = ipn_data.get("actually_paid_currency")
                payment.txn_id = ipn_data.get("outcome", {}).get("txid")
                payment.network = ipn_data.get("outcome", {}).get("network")
                payment.updated_at = datetime.now(timezone.utc)
                
                # Update order status if payment is finished
                if new_status == PaymentStatus.FINISHED and old_status != PaymentStatus.FINISHED:
                    from database.models import OrderStatus
                    payment.order.payment_status = PaymentStatus.FINISHED
                    payment.order.status = OrderStatus.PAID
                    payment.order.updated_at = datetime.now(timezone.utc)
                    
                    # Award loyalty points
                    await self._award_loyalty_points(payment.order)
                    
                    # Process digital delivery
                    if payment.order.items:
                        await self._process_digital_delivery(payment.order)
                
                db.commit()
                
                logger.info(f"Updated payment {payment_id} status: {old_status} -> {new_status}")
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to process IPN callback: {e}")
            return False
    
    async def create_qr_payment_data(self, payment_data: Dict[str, Any]) -> Dict[str, str]:
        """Create QR code data for payment."""
        try:
            pay_address = payment_data.get("pay_address")
            pay_amount = payment_data.get("pay_amount")
            pay_currency = payment_data.get("pay_currency", "").upper()
            
            if not pay_address or not pay_amount:
                return {}
            
            # Create payment URI for QR code
            payment_uri = f"{pay_currency.lower()}:{pay_address}"
            if pay_amount:
                payment_uri += f"?amount={pay_amount}"
            
            return {
                "payment_uri": payment_uri,
                "pay_address": pay_address,
                "pay_amount": str(pay_amount),
                "pay_currency": pay_currency,
                "qr_data": payment_uri
            }
            
        except Exception as e:
            logger.error(f"Failed to create QR payment data: {e}")
            return {}
    
    async def _award_loyalty_points(self, order: Order) -> None:
        """Award loyalty points for completed order."""
        try:
            from database.database import SessionLocal
            from database.models import LoyaltyTransaction
            
            # Award 1 point per dollar spent (configurable)
            points_earned = int(order.total_amount)
            
            if points_earned <= 0:
                return
            
            db = SessionLocal()
            try:
                # Update user's loyalty points
                order.user.loyalty_points += points_earned
                order.user.total_spent += order.total_amount
                order.user.total_orders += 1
                
                # Create loyalty transaction record
                loyalty_transaction = LoyaltyTransaction(
                    user_id=order.user_id,
                    order_id=order.id,
                    points=points_earned,
                    type="earned",
                    description=f"Points earned from order {order.order_number}",
                    reference=f"order_{order.id}"
                )
                
                db.add(loyalty_transaction)
                db.commit()
                
                logger.info(f"Awarded {points_earned} loyalty points to user {order.user_id}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to award loyalty points: {e}")
    
    async def _process_digital_delivery(self, order: Order) -> None:
        """Process digital product delivery."""
        try:
            from database.models import ProductType
            
            for item in order.items:
                if item.product.product_type == ProductType.DIGITAL:
                    # Generate download links with expiration
                    expiry_date = datetime.now(timezone.utc) + timedelta(
                        days=item.product.download_expiry_days or 30
                    )
                    
                    download_links = []
                    if item.product.digital_file_url:
                        download_token = uuid.uuid4().hex
                        download_links.append({
                            "url": f"{settings.webhook_url}/download/{download_token}",
                            "token": download_token,
                            "expires_at": expiry_date.isoformat(),
                            "download_limit": item.product.download_limit or 5
                        })
                    
                    item.download_links = download_links
                    item.download_expires_at = expiry_date
            
            from database.database import SessionLocal
            db = SessionLocal()
            try:
                db.commit()
                logger.info(f"Processed digital delivery for order {order.order_number}")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to process digital delivery: {e}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API headers for NOWPayments requests."""
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "TelegramShopBot/1.0"
        }
    
    async def estimate_payment_amount(
        self, 
        amount: float, 
        from_currency: str, 
        to_currency: str
    ) -> Optional[Dict[str, Any]]:
        """Estimate payment amount for currency conversion."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/estimate",
                    headers=self._get_headers(),
                    params={
                        "amount": amount,
                        "currency_from": from_currency.lower(),
                        "currency_to": to_currency.lower()
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to estimate payment amount: {e}")
            return None
    
    async def get_payment_history(
        self, 
        limit: int = 10, 
        page: int = 0,
        sort_by: str = "created_at",
        order_by: str = "desc"
    ) -> Optional[Dict[str, Any]]:
        """Get payment history from NOWPayments."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v1/payment",
                    headers=self._get_headers(),
                    params={
                        "limit": limit,
                        "page": page,
                        "sortBy": sort_by,
                        "orderBy": order_by
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get payment history: {e}")
            return None


# Global service instance
nowpayments_service = NOWPaymentsService()
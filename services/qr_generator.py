"""
QR Code generation service for payment invoices.
"""
import base64
import io
from typing import Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont
import qrcode
from qrcode.image.pil import PilImage
from loguru import logger


class QRCodeGenerator:
    """Service for generating QR codes for cryptocurrency payments."""
    
    def __init__(self):
        self.default_size = (300, 300)
        self.default_border = 4
        self.default_box_size = 10
        
    def generate_payment_qr(
        self,
        payment_data: str,
        size: tuple = None,
        border: int = None,
        box_size: int = None,
        logo_path: Optional[str] = None,
        add_payment_info: bool = True,
        payment_amount: Optional[str] = None,
        payment_currency: Optional[str] = None,
        payment_address: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Generate QR code for cryptocurrency payment.
        
        Args:
            payment_data: Payment URI or address
            size: QR code image size (width, height)
            border: Border size around QR code
            box_size: Size of each QR code box
            logo_path: Path to logo image to embed in center
            add_payment_info: Whether to add payment info text below QR
            payment_amount: Payment amount for display
            payment_currency: Payment currency for display
            payment_address: Payment address for display
            
        Returns:
            QR code image as bytes
        """
        try:
            size = size or self.default_size
            border = border or self.default_border
            box_size = box_size or self.default_box_size
            
            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=box_size,
                border=border,
            )
            
            # Add data to QR code
            qr.add_data(payment_data)
            qr.make(fit=True)
            
            # Generate QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to PIL Image for editing
            qr_img = qr_img.convert("RGB")
            
            # Add logo if provided
            if logo_path:
                qr_img = self._add_logo_to_qr(qr_img, logo_path)
            
            # Add payment information if requested
            if add_payment_info and any([payment_amount, payment_currency, payment_address]):
                qr_img = self._add_payment_info_to_qr(
                    qr_img, payment_amount, payment_currency, payment_address
                )
            
            # Resize to desired size
            qr_img = qr_img.resize(size, Image.Resampling.LANCZOS)
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            qr_img.save(img_buffer, format='PNG', quality=95)
            img_buffer.seek(0)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to generate payment QR code: {e}")
            return None
    
    def generate_simple_qr(
        self,
        data: str,
        size: tuple = None,
        error_correction: str = "M"
    ) -> Optional[bytes]:
        """
        Generate simple QR code without additional styling.
        
        Args:
            data: Data to encode in QR code
            size: QR code image size
            error_correction: Error correction level (L, M, Q, H)
            
        Returns:
            QR code image as bytes
        """
        try:
            size = size or self.default_size
            
            # Map error correction levels
            error_levels = {
                "L": qrcode.constants.ERROR_CORRECT_L,
                "M": qrcode.constants.ERROR_CORRECT_M, 
                "Q": qrcode.constants.ERROR_CORRECT_Q,
                "H": qrcode.constants.ERROR_CORRECT_H,
            }
            
            error_correct = error_levels.get(error_correction.upper(), 
                                           qrcode.constants.ERROR_CORRECT_M)
            
            # Create and generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=error_correct,
                box_size=self.default_box_size,
                border=self.default_border,
            )
            
            qr.add_data(data)
            qr.make(fit=True)
            
            # Generate image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img = qr_img.resize(size, Image.Resampling.LANCZOS)
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to generate simple QR code: {e}")
            return None
    
    def generate_qr_with_branding(
        self,
        data: str,
        brand_color: str = "#000000",
        background_color: str = "#FFFFFF",
        logo_path: Optional[str] = None,
        brand_text: Optional[str] = None,
        size: tuple = None
    ) -> Optional[bytes]:
        """
        Generate branded QR code with custom colors and branding.
        
        Args:
            data: Data to encode
            brand_color: Color for QR code modules
            background_color: Background color
            logo_path: Path to logo image
            brand_text: Brand text to add below QR
            size: Image size
            
        Returns:
            Branded QR code image as bytes
        """
        try:
            size = size or self.default_size
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=self.default_box_size,
                border=self.default_border,
            )
            
            qr.add_data(data)
            qr.make(fit=True)
            
            # Generate with custom colors
            qr_img = qr.make_image(
                fill_color=brand_color,
                back_color=background_color
            ).convert("RGB")
            
            # Add logo
            if logo_path:
                qr_img = self._add_logo_to_qr(qr_img, logo_path)
            
            # Add brand text
            if brand_text:
                qr_img = self._add_brand_text(qr_img, brand_text, brand_color)
            
            # Resize
            qr_img = qr_img.resize(size, Image.Resampling.LANCZOS)
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            qr_img.save(img_buffer, format='PNG', quality=95)
            img_buffer.seek(0)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to generate branded QR code: {e}")
            return None
    
    def _add_logo_to_qr(self, qr_img: Image.Image, logo_path: str) -> Image.Image:
        """Add logo to center of QR code."""
        try:
            logo = Image.open(logo_path)
            
            # Calculate logo size (10% of QR code size)
            qr_width, qr_height = qr_img.size
            logo_size = min(qr_width, qr_height) // 10
            
            # Resize logo
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Create white background for logo
            bg_size = logo_size + 20
            bg = Image.new('RGB', (bg_size, bg_size), 'white')
            
            # Paste logo on background
            logo_pos = ((bg_size - logo_size) // 2, (bg_size - logo_size) // 2)
            bg.paste(logo, logo_pos)
            
            # Paste background with logo on QR code
            qr_pos = ((qr_width - bg_size) // 2, (qr_height - bg_size) // 2)
            qr_img.paste(bg, qr_pos)
            
            return qr_img
            
        except Exception as e:
            logger.error(f"Failed to add logo to QR code: {e}")
            return qr_img
    
    def _add_payment_info_to_qr(
        self,
        qr_img: Image.Image,
        amount: Optional[str],
        currency: Optional[str],
        address: Optional[str]
    ) -> Image.Image:
        """Add payment information text below QR code."""
        try:
            qr_width, qr_height = qr_img.size
            text_height = 100
            
            # Create new image with space for text
            new_img = Image.new('RGB', (qr_width, qr_height + text_height), 'white')
            new_img.paste(qr_img, (0, 0))
            
            # Draw text
            draw = ImageDraw.Draw(new_img)
            
            try:
                font_large = ImageFont.truetype("arial.ttf", 16)
                font_small = ImageFont.truetype("arial.ttf", 12)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            y_offset = qr_height + 10
            
            # Add amount and currency
            if amount and currency:
                amount_text = f"Amount: {amount} {currency.upper()}"
                text_bbox = draw.textbbox((0, 0), amount_text, font=font_large)
                text_width = text_bbox[2] - text_bbox[0]
                x_pos = (qr_width - text_width) // 2
                draw.text((x_pos, y_offset), amount_text, fill='black', font=font_large)
                y_offset += 25
            
            # Add address (truncated)
            if address:
                if len(address) > 20:
                    address_text = f"Address: {address[:10]}...{address[-10:]}"
                else:
                    address_text = f"Address: {address}"
                
                text_bbox = draw.textbbox((0, 0), address_text, font=font_small)
                text_width = text_bbox[2] - text_bbox[0]
                x_pos = (qr_width - text_width) // 2
                draw.text((x_pos, y_offset), address_text, fill='gray', font=font_small)
            
            return new_img
            
        except Exception as e:
            logger.error(f"Failed to add payment info to QR code: {e}")
            return qr_img
    
    def _add_brand_text(
        self,
        qr_img: Image.Image,
        brand_text: str,
        text_color: str = "#000000"
    ) -> Image.Image:
        """Add brand text below QR code."""
        try:
            qr_width, qr_height = qr_img.size
            text_height = 50
            
            # Create new image with space for text
            new_img = Image.new('RGB', (qr_width, qr_height + text_height), 'white')
            new_img.paste(qr_img, (0, 0))
            
            # Draw brand text
            draw = ImageDraw.Draw(new_img)
            
            try:
                font = ImageFont.truetype("arial.ttf", 18)
            except:
                font = ImageFont.load_default()
            
            text_bbox = draw.textbbox((0, 0), brand_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            x_pos = (qr_width - text_width) // 2
            y_pos = qr_height + 15
            
            draw.text((x_pos, y_pos), brand_text, fill=text_color, font=font)
            
            return new_img
            
        except Exception as e:
            logger.error(f"Failed to add brand text to QR code: {e}")
            return qr_img
    
    def qr_to_base64(self, qr_bytes: bytes) -> str:
        """Convert QR code bytes to base64 string."""
        try:
            return base64.b64encode(qr_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to convert QR to base64: {e}")
            return ""
    
    def create_payment_qr_data(
        self,
        payment_uri: str,
        amount: Optional[str] = None,
        currency: Optional[str] = None,
        address: Optional[str] = None,
        message: Optional[str] = None,
        label: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create comprehensive payment QR code data.
        
        Returns dict with QR code image, base64, and metadata.
        """
        try:
            # Generate QR code image
            qr_bytes = self.generate_payment_qr(
                payment_data=payment_uri,
                add_payment_info=True,
                payment_amount=amount,
                payment_currency=currency,
                payment_address=address
            )
            
            if not qr_bytes:
                return {}
            
            # Convert to base64 for web display
            qr_base64 = self.qr_to_base64(qr_bytes)
            
            return {
                "qr_code_bytes": qr_bytes,
                "qr_code_base64": qr_base64,
                "qr_code_data_uri": f"data:image/png;base64,{qr_base64}",
                "payment_uri": payment_uri,
                "metadata": {
                    "amount": amount,
                    "currency": currency,
                    "address": address,
                    "message": message,
                    "label": label,
                    "format": "PNG",
                    "size": self.default_size
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to create payment QR data: {e}")
            return {}


# Global service instance
qr_generator = QRCodeGenerator()
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from supabase import create_client, Client
import qrcode
from io import BytesIO
import os
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI application
app = FastAPI(
    title="WatchMe QR Code Generator API",
    description="Generate QR codes for device sharing",
    version="1.0.0"
)

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "watchme-avatars")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")

# S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Response models
class QRCodeResponse(BaseModel):
    qrCodeUrl: str

# QR Code settings
QR_CODE_SIZE = 512
QR_CODE_BOX_SIZE = 10
QR_CODE_BORDER = 2

def check_device_exists(device_id: str) -> bool:
    """
    Check if device exists in database
    """
    try:
        result = supabase.table('devices').select('device_id').eq('device_id', device_id).execute()
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Device existence check failed: {str(e)}")
        return False

def generate_qrcode(device_id: str) -> bytes:
    """
    Generate QR code image (PNG format)
    Encodes only the device_id (UUID)
    """
    try:
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=QR_CODE_BOX_SIZE,
            border=QR_CODE_BORDER,
        )

        # Add device_id as data
        qr.add_data(device_id)
        qr.make(fit=True)

        # Generate image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return buffer.getvalue()
    except Exception as e:
        logger.error(f"QR code generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="QR code generation failed")

def upload_to_s3(file_content: bytes, s3_key: str) -> str:
    """
    Upload QR code image to S3 with public-read ACL
    """
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            ContentType='image/png',
            CacheControl='public, max-age=31536000',
            ACL='public-read'  # Make QR code image publicly accessible
        )

        # Generate S3 URL
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        return s3_url
    except ClientError as e:
        logger.error(f"S3 upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="S3 upload failed")

def delete_from_s3(s3_key: str) -> None:
    """
    Delete QR code image from S3
    """
    try:
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
    except ClientError as e:
        logger.error(f"S3 deletion failed: {str(e)}")
        # Deletion failure is not critical, just log

def update_database(device_id: str, qr_code_url: Optional[str]) -> None:
    """
    Update qr_code_url in devices table
    """
    try:
        supabase.table("devices").update(
            {"qr_code_url": qr_code_url}
        ).eq("device_id", device_id).execute()
    except Exception as e:
        logger.error(f"Database update failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Database update failed")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "qr-code-generator-api"
    }

@app.post("/v1/devices/{device_id}/qrcode", response_model=QRCodeResponse)
async def generate_device_qrcode(device_id: str):
    """
    Generate QR code for device sharing

    - Validates device existence
    - Generates QR code image (PNG)
    - Uploads to S3
    - Updates database
    """

    # Check if device exists
    if not check_device_exists(device_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # Generate QR code
    qr_image_bytes = generate_qrcode(device_id)

    # S3 key
    s3_key = f"devices/{device_id}/qrcode.png"

    # Upload to S3
    s3_url = upload_to_s3(qr_image_bytes, s3_key)

    # Update database
    try:
        update_database(device_id, s3_url)
    except HTTPException:
        # Rollback: delete from S3 if DB update fails
        delete_from_s3(s3_key)
        raise

    logger.info(f"QR code generated: device_id={device_id}, url={s3_url}")
    return QRCodeResponse(qrCodeUrl=s3_url)

@app.delete("/v1/devices/{device_id}/qrcode", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device_qrcode(device_id: str):
    """
    Delete QR code for device
    """
    # Check if device exists
    if not check_device_exists(device_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    s3_key = f"devices/{device_id}/qrcode.png"

    # Delete from S3
    delete_from_s3(s3_key)

    # Update database
    update_database(device_id, None)

    logger.info(f"QR code deleted: device_id={device_id}")

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General error handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8021))
    host = os.getenv("API_HOST", "0.0.0.0")
    uvicorn.run("app:app", host=host, port=port, reload=True)

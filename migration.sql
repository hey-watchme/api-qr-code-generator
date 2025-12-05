-- Migration: Add qr_code_url column to devices table
-- Date: 2025-12-05
-- Description: Stores QR code image URL for device sharing

-- Add qr_code_url column to devices table
ALTER TABLE devices
ADD COLUMN IF NOT EXISTS qr_code_url TEXT;

-- Add index for faster lookups (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_devices_qr_code_url ON devices(qr_code_url);

-- Add comment to document the column
COMMENT ON COLUMN devices.qr_code_url IS 'S3 URL of the QR code image for device sharing';

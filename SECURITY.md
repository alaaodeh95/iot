# IoT Smart Home Security Guide

## Security Features Implemented

### 1. Authentication & Authorization
- **API Key Authentication**: Required for system endpoints
- **JWT Tokens**: Device-specific authentication with expiration
- **Device Keys**: Unique keys per sensor device
- **Gateway Authentication**: Separate key for gateway service

### 2. Data Protection
- **Request Signing**: HMAC-SHA256 signatures for data integrity
- **Optional Encryption**: AES encryption for sensitive sensor data
- **Secure Headers**: Security headers to prevent common attacks

### 3. Network Security
- **HTTPS Support**: SSL/TLS encryption for all communications
- **Certificate Validation**: Verify SSL certificates
- **Rate Limiting**: Prevent abuse with request rate limits

### 4. Access Control
- **Device Isolation**: Each device has unique credentials
- **Endpoint Protection**: Different authentication levels per endpoint
- **Token Expiration**: JWT tokens automatically expire

## API Endpoints Security

### Device Authentication Required:
- `POST /api/sensor-data` - Requires JWT token + signature
- Device must authenticate before sending sensor data

### API Key Required:
- `GET /api/status` - System status
- `POST /api/actuators/<id>` - Actuator control
- `POST /api/device/token` - Generate device tokens

### Gateway Authentication Required:
- `POST /api/sensor-data/gateway` - Gateway-filtered data

## Usage Instructions

### 1. Generate Device Token
```bash
curl -X POST http://localhost:5000/api/device/token \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "roof_station"}'
```

### 2. Send Sensor Data
```bash
curl -X POST http://localhost:5000/api/sensor-data \
  -H "Authorization: Bearer JWT_TOKEN" \
  -H "X-Signature: REQUEST_SIGNATURE" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "roof_station", "readings": [...]}'
```

### 3. Enable HTTPS
1. Set `SSL_ENABLED=true` in .env
2. Ensure certificates exist in ./certs/
3. Update client URLs to use https://

## Security Best Practices

1. **Environment Variables**: Store all keys in .env file
2. **Certificate Management**: Use proper CA-signed certificates in production
3. **Key Rotation**: Regularly rotate API keys and JWT secrets
4. **Monitoring**: Monitor failed authentication attempts
5. **Network**: Use VPN or private networks when possible

## Troubleshooting

### Authentication Errors
- Check device keys in configuration
- Verify JWT token hasn't expired
- Ensure request signature is correctly calculated

### SSL/TLS Issues
- Verify certificate files exist and are readable
- Check certificate validity dates
- Ensure proper certificate chain

### Rate Limiting
- Check if device is exceeding rate limits
- Increase limits if legitimate traffic is blocked

# Stock Data API

API cung cấp dữ liệu chứng khoán Việt Nam, tập trung vào các phiên giao dịch gần đây.

## API Endpoints

### Lấy thông tin 7 phiên gần nhất của một mã chứng khoán

```
GET /recent/{symbol}?days={days}
```

- `{symbol}`: Mã chứng khoán (mặc định: PDR)
- `{days}`: Số phiên muốn lấy (mặc định: 7)

Ví dụ:
```
GET /recent/VCB?days=10
GET /recent/PDR
GET /recent  # Mặc định sẽ lấy PDR
```

### Kiểm tra trạng thái API

```
GET /health
```

### Mô tả dữ liệu trả về

```json
{
  "symbol": "PDR",
  "days": 7,
  "sessions": [
    {
      "date": "2025-07-08",
      "open": 19.05,
      "close": 18.85,
      "high": 19.15,
      "low": 18.6,
      "volume": 14178300,
      "ceiling": 20.17,
      "floor": 17.53,
      "is_today": false
    },
    ...
    {
      "date": "2025-07-16",
      "open": 19.35,
      "close": 20.05,
      "high": 20.2,
      "low": 19.3,
      "volume": 13756700,
      "ceiling": 21.45,
      "floor": 18.65,
      "is_today": true,
      "current_price": 20.05
    }
  ],
  "timestamp": "2025-07-16T11:18:29.460764"
}
```

## Chạy API localy

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy API
python api.py
```

API sẽ chạy tại `http://localhost:8000` 
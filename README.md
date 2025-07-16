# Stock Data API

API cung cấp dữ liệu chứng khoán Việt Nam, tập trung vào các phiên giao dịch gần đây.

## API Endpoints

### 1. Lấy dữ liệu ngày hôm nay của một mã chứng khoán

```
GET /stock/{symbol}
```

- `{symbol}`: Mã chứng khoán (mặc định: PDR)

Trả về dữ liệu ngày hôm nay và ngày hôm qua, bao gồm giá và khối lượng giao dịch.

Ví dụ:
```
GET /stock/VCB
GET /stock/PDR
```

### 2. Lấy dữ liệu nhiều ngày gần đây của một mã chứng khoán

Có 2 cách:

```
GET /stock/{symbol}?recent={days}
GET /stock/{symbol}/recent?days={days}
```

- `{symbol}`: Mã chứng khoán (mặc định: PDR)
- `{days}`: Số phiên muốn lấy (mặc định: 7)

Ví dụ:
```
GET /stock/VCB?recent=10
GET /stock/PDR/recent?days=5
```

### 3. Lấy dữ liệu trong khoảng thời gian cụ thể

```
GET /stock/{symbol}/day-range?start_date={start_date}&end_date={end_date}
```

- `{symbol}`: Mã chứng khoán
- `{start_date}`: Ngày bắt đầu (định dạng YYYY-MM-DD)
- `{end_date}`: Ngày kết thúc (định dạng YYYY-MM-DD)

Ví dụ:
```
GET /stock/VCB/day-range?start_date=2025-01-01&end_date=2025-01-31
```

### 4. Kiểm tra trạng thái API

```
GET /health
```

## Mô tả dữ liệu trả về

### Dữ liệu ngày hôm nay `/stock/{symbol}`

```json
{
  "symbol": "PDR",
  "data": {
    "today": {
      "date": "2025-07-16",
      "open": 19.35,
      "close": 20.05,
      "high": 20.2,
      "low": 19.3,
      "volume": 13756700,
      "current_price": 20.05
    },
    "yesterday": {
      "date": "2025-07-15",
      "close": 19.4,
      "volume": 15996300
    }
  },
  "timestamp": "2025-07-16T12:34:56.789012"
}
```

### Dữ liệu nhiều ngày `/stock/{symbol}/recent`

```json
{
  "symbol": "PDR",
  "days": 7,
  "sessions": [
    {
      "date": "2025-07-10",
      "open": 19.25,
      "close": 19.1,
      "high": 19.65,
      "low": 19.0,
      "volume": 18183200,
      "ceiling": 20.44,
      "floor": 17.76,
      "is_today": false
    },
    // ... các phiên khác
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
  "timestamp": "2025-07-16T12:34:56.789012"
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

## Deploy lên Railway

1. Đảm bảo các file cấu hình đã có: `Procfile`, `requirements.txt`, `runtime.txt`
2. Push code lên GitHub
3. Kết nối với Railway và deploy từ GitHub repository
4. Railway sẽ tự động build và deploy ứng dụng 
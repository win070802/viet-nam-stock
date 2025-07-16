from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from vnstock import Vnstock
from config import settings

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Stock Data API",
    description="Real-time stock data API for Vietnamese stock market",
    version="2.1.0"
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Stock Data API is running", "version": "2.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "stock-api"}

@app.get("/stock/{symbol}")
async def get_stock_today(symbol: str = "PDR", recent: Optional[int] = None):
    """
    Lấy dữ liệu ngày hôm nay của một mã chứng khoán
    Nếu có tham số recent, sẽ lấy dữ liệu của n ngày gần đây
    """
    if recent:
        return await get_stock_recent(symbol, recent)
    
    try:
        symbol = symbol.upper()
        
        # Lấy dữ liệu ngày hôm nay và hôm qua
        loop = asyncio.get_event_loop()
        
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        today_str = today.strftime('%Y-%m-%d')
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        
        # Hàm lấy dữ liệu ngày hôm nay và hôm qua
        def get_stock_data():
            try:
                stock = Vnstock().stock(symbol=symbol, source='VCI')
                # Lấy dữ liệu 2 ngày gần nhất để có ngày hôm nay và hôm qua
                data = stock.quote.history(start=yesterday_str, end=today_str, interval='1D')
                
                if data.empty:
                    # Thử lùi thêm 5 ngày nếu không có dữ liệu
                    start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
                    data = stock.quote.history(start=start_date, end=today_str, interval='1D')
                
                # Sort theo thời gian giảm dần (mới nhất đầu tiên)
                data = data.sort_values('time', ascending=False)
                
                # Lấy giá realtime nếu có
                current_price = None
                try:
                    intraday = stock.quote.intraday()
                    if not intraday.empty:
                        current_price = intraday['price'].iloc[-1]
                except:
                    pass
                
                result = {}
                
                # Dữ liệu hôm nay
                if not data.empty:
                    today_data = data.iloc[0]
                    result["today"] = {
                        "date": today_data['time'].strftime('%Y-%m-%d'),
                        "open": float(today_data['open']),
                        "close": float(today_data['close']),
                        "high": float(today_data['high']),
                        "low": float(today_data['low']),
                        "volume": int(today_data['volume']),
                        "current_price": float(current_price) if current_price else float(today_data['close'])
                    }
                    
                    # Dữ liệu hôm qua nếu có
                    if len(data) > 1:
                        yesterday_data = data.iloc[1]
                        result["yesterday"] = {
                            "date": yesterday_data['time'].strftime('%Y-%m-%d'),
                            "close": float(yesterday_data['close']),
                            "volume": int(yesterday_data['volume'])
                        }
                
                return result
            except Exception as e:
                logger.error(f"Lỗi khi lấy dữ liệu chứng khoán: {str(e)}")
                return {}
        
        # Lấy dữ liệu ngày hôm nay và hôm qua
        stock_data = await loop.run_in_executor(None, get_stock_data)
        
        if not stock_data:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy dữ liệu cho mã {symbol}")
        
        return {
            "symbol": symbol,
            "data": stock_data,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi lấy dữ liệu cho {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server: {str(e)}")

@app.get("/stock/{symbol}/recent")
async def get_stock_recent(symbol: str, days: int = 7):
    """
    Lấy dữ liệu n ngày gần đây của một mã chứng khoán
    """
    try:
        symbol = symbol.upper()
        
        # Tính ngày kết thúc (hôm nay) và ngày bắt đầu (lùi 30 ngày để đảm bảo đủ số phiên)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Chuyển hàm blocking sang async để không chặn event loop
        loop = asyncio.get_event_loop()
        
        def get_recent_data():
            try:
                # Lấy dữ liệu lịch sử
                stock = Vnstock().stock(symbol=symbol, source='VCI')
                history_df = stock.quote.history(start=start_date, end=end_date, interval='1D')
                
                if history_df.empty:
                    return []
                    
                # Chỉ lấy N phiên gần nhất
                recent_df = history_df.sort_values('time', ascending=False).head(days).sort_values('time')
                
                # Format lại dữ liệu để trả về
                result = []
                today = datetime.now().strftime('%Y-%m-%d')
                
                for i, row in recent_df.iterrows():
                    session_date = pd.to_datetime(row['time']).strftime('%Y-%m-%d')
                    session_data = {
                        'date': session_date,
                        'open': float(row['open']),
                        'close': float(row['close']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'volume': int(row['volume']),
                        # Tính giá trần, sàn (±7% so với giá tham chiếu)
                        'ceiling': round(float(row['close']) * 1.07, 2),
                        'floor': round(float(row['close']) * 0.93, 2),
                        'is_today': session_date == today
                    }
                    
                    # Nếu là phiên hôm nay, lấy thêm giá hiện tại
                    if session_date == today:
                        try:
                            # Lấy giá hiện tại
                            intraday = stock.quote.intraday()
                            if not intraday.empty:
                                session_data['current_price'] = float(intraday['price'].iloc[-1])
                            else:
                                session_data['current_price'] = float(row['close'])
                        except:
                            session_data['current_price'] = float(row['close'])
                    
                    result.append(session_data)
                    
                return result
            except Exception as e:
                logger.error(f"Lỗi khi lấy dữ liệu gần đây: {str(e)}")
                return []
        
        data = await loop.run_in_executor(None, get_recent_data)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy dữ liệu cho mã {symbol} trong {days} phiên gần đây")
        
        return {
            "symbol": symbol,
            "days": days,
            "sessions": data,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi lấy dữ liệu phiên giao dịch cho {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server: {str(e)}")

@app.get("/stock/{symbol}/day-range")
async def get_stock_range(
    symbol: str, 
    start_date: str = Query(..., description="Ngày bắt đầu (YYYY-MM-DD)"), 
    end_date: str = Query(..., description="Ngày kết thúc (YYYY-MM-DD)")
):
    """
    Lấy dữ liệu từ ngày start_date đến ngày end_date
    """
    try:
        symbol = symbol.upper()
        
        # Xác thực ngày tháng
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Định dạng ngày không hợp lệ. Sử dụng định dạng YYYY-MM-DD")
        
        # Lấy dữ liệu trong khoảng thời gian
        loop = asyncio.get_event_loop()
        
        def get_range_data():
            try:
                stock = Vnstock().stock(symbol=symbol, source='VCI')
                data = stock.quote.history(start=start_date, end=end_date, interval='1D')
                
                if data.empty:
                    return []
                
                # Sort theo thời gian tăng dần
                data = data.sort_values('time', ascending=True)
                
                # Chuyển đổi dữ liệu
                result = []
                for _, row in data.iterrows():
                    session_date = row['time'].strftime('%Y-%m-%d')
                    session_data = {
                        'date': session_date,
                        'open': float(row['open']),
                        'close': float(row['close']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'volume': int(row['volume']),
                        # Tính giá trần, sàn (±7% so với giá tham chiếu)
                        'ceiling': round(float(row['close']) * 1.07, 2),
                        'floor': round(float(row['close']) * 0.93, 2)
                    }
                    result.append(session_data)
                
                return result
            except Exception as e:
                logger.error(f"Lỗi khi lấy dữ liệu khoảng thời gian: {str(e)}")
                return []
        
        # Lấy dữ liệu trong khoảng thời gian
        range_data = await loop.run_in_executor(None, get_range_data)
        
        if not range_data:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy dữ liệu cho mã {symbol} từ {start_date} đến {end_date}")
        
        return {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "sessions": range_data,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lỗi khi lấy dữ liệu khoảng thời gian cho {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi nội bộ server: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)

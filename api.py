from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from recent_price import get_recent_sessions

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Stock Data API",
    description="Real-time stock data API for Vietnamese stock market",
    version="1.0.0"
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Stock Data API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "stock-api"}

@app.get("/recent")
@app.get("/recent/{symbol}")
async def get_recent_data(symbol: str = "PDR", days: int = 7):
    """
    Lấy dữ liệu N phiên gần nhất (mặc định 7 phiên)
    Nếu không truyền mã, mặc định sẽ lấy mã PDR
    """
    try:
        symbol = symbol.upper()
        
        # Chuyển hàm blocking sang async để không chặn event loop
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: get_recent_sessions(symbol, days))
        
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

@app.get("/pdr/recent")
async def get_pdr_recent():
    """
    Shortcut để lấy 7 phiên gần nhất của PDR
    """
    return await get_recent_data("PDR")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
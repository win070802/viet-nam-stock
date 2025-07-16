from datetime import datetime, timedelta
from vnstock import Vnstock
import pandas as pd

def get_recent_sessions(symbol, days=7, source='VCI'):
    """
    Lấy dữ liệu N phiên gần nhất của một mã chứng khoán
    
    Args:
        symbol (str): Mã chứng khoán (VD: PDR)
        days (int): Số phiên muốn lấy (mặc định: 7)
        source (str): Nguồn dữ liệu (mặc định: VCI)
        
    Returns:
        list: Danh sách các phiên giao dịch dạng dict
    """
    try:
        # Tính ngày kết thúc (hôm nay) và ngày bắt đầu (lùi 30 ngày để đảm bảo đủ số phiên)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Lấy dữ liệu lịch sử
        stock = Vnstock().stock(symbol=symbol, source=source)
        history_df = stock.quote.history(start=start_date, end=end_date, interval='1D')
        
        # Chỉ lấy N phiên gần nhất
        recent_df = history_df.sort_values('time', ascending=False).head(days).sort_values('time')
        
        # Format lại dữ liệu để trả về
        result = []
        today = datetime.now().strftime('%Y-%m-%d')
        
        for i, row in recent_df.iterrows():
            session_date = pd.to_datetime(row['time']).strftime('%Y-%m-%d')
            session_data = {
                'date': session_date,
                'open': row['open'],
                'close': row['close'],
                'high': row['high'],
                'low': row['low'],
                'volume': int(row['volume']),
                # Tính giá trần, sàn (±7% so với giá tham chiếu)
                'ceiling': round(row['close'] * 1.07, 2),
                'floor': round(row['close'] * 0.93, 2),
                'is_today': session_date == today
            }
            
            # Nếu là phiên hôm nay, lấy thêm giá hiện tại
            if session_date == today:
                try:
                    # Lấy giá hiện tại
                    intraday = stock.quote.intraday()
                    if not intraday.empty:
                        session_data['current_price'] = intraday['price'].iloc[-1]
                    else:
                        session_data['current_price'] = row['close']
                except:
                    session_data['current_price'] = row['close']
            
            result.append(session_data)
            
        return result
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

if __name__ == "__main__":
    # Test với mã PDR
    data = get_recent_sessions("PDR")
    for session in data:
        print(session) 
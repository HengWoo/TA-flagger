import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from analysis import load_data, perform_analysis
import logging
import traceback
import pandas as pd
import json
import io

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bxe5yt5f-k2pi6sse-e051mmibm308.ac1-preview.marscode.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.Timestamp):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif pd.isna(obj):
            return None
        return super().default(obj)

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "欢迎使用糖期权分析 API"}

@app.get("/api/sugar-options-data")
async def get_sugar_options_data():
    try:
        csv_path = "/cloudide/workspace/sugar-quant/TA-flagger/data/sugar 60 mins.csv"
        
        logger.info(f"Attempting to load data from: {csv_path}")
        
        if not os.path.exists(csv_path):
            logger.error(f"File not found at {csv_path}")
            raise FileNotFoundError(f"CSV file not found at {csv_path}")
        
        df = load_data(csv_path)
        logger.info(f"Data loaded successfully. Shape: {df.shape}")
        
        logger.info("Performing analysis...")
        data, indicator_data, signals, trades = perform_analysis(df)
        logger.info("Analysis completed successfully")
        
        def generate():
            yield json.dumps({
                "data": data,
                "indicatorData": indicator_data,
                "signals": signals,
                "trades": trades
            }, cls=CustomJSONEncoder)
        
        return StreamingResponse(generate(), media_type="application/json")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"发生意外错误: {str(e)}\n\n{traceback.format_exc()}")

@app.get("/inspect-csv")
async def inspect_csv():
    try:
        csv_path = "/cloudide/workspace/sugar-quant/TA-flagger/data/sugar 60 mins.csv"
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found at {csv_path}")
        
        # Read the first few lines of the CSV file
        with open(csv_path, 'r') as file:
            head = [next(file) for _ in range(5)]
        
        # Read the CSV file
        df = pd.read_csv(csv_path, nrows=5)
        
        return {
            "file_path": csv_path,
            "file_size": os.path.getsize(csv_path),
            "first_few_lines": head,
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.apply(lambda x: str(x)).to_dict(),
            "sample_data": df.to_dict(orient='records')
        }
    except Exception as e:
        logger.error(f"An error occurred while inspecting the CSV: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"检查 CSV 时发生错误: {str(e)}\n\n{traceback.format_exc()}")

@app.get("/test")
async def test():
    logger.info("Test endpoint accessed")
    return {"message": "测试路由正常工作"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting the FastAPI application")
    uvicorn.run(app, host="0.0.0.0", port=8000)
# Sugar Options Analysis

This project provides a technical analysis dashboard for sugar options trading data.

## Setup

### Frontend

1. Navigate to the `frontend` directory
2. Install dependencies:
   ```
   npm install
   ```
3. Start the development server:
   ```
   npm start
   ```

### Backend

1. Navigate to the `backend` directory
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Start the FastAPI server:
   ```
   uvicorn app:app --reload
   ```

## Usage

Open your browser and navigate to `http://localhost:3000` to view the dashboard. The backend API will be available at `http://localhost:8000`.

## Data

The analysis uses the data from `data/sugar_60_mins_sample.csv`. Make sure this file is present and up-to-date.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
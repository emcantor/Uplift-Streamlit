There are 3 files that need to keep running:

- frontend/main.py: run with: nohup streamlit run main.py --server.port 8503 >> server.log 2>&1 &
- backend/recurring.py: run with: nohup python3 recurring.py >> nohup_recurring.log 2>&1 &
- backend/run.py: this function is running every minute from the crontab

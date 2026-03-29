Run Backend on one terminal with

cd ~/Desktop/"COE892 Project"/smart-parking-system/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ~/Desktop/"COE892 Project"/smart-parking-system/backend
source venv/bin/activate
python start_services.py

Run frontend on another terminal with

cd ~/Desktop/"COE892 Project"/smart-parking-system/frontend
npm install       # only needed the first time
npm run dev

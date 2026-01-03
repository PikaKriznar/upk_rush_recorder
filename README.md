# upk_rush_recorder

This repository contains a real-time demo and visualization app for the *Rush Index* project based on the WISDM dataset.

---

## Requirements
- Python environment (`wisdm-env`) already created
- Required packages installed (`fastapi`, `uvicorn`, `streamlit` and all modules/libraries used in this project)
- Project and dataset structure already set up

---

## 1. Start the real-time backend (API server)

From the project root, activate the environment and start the FastAPI server:

```bash
cd wisdm-dataset
source wisdm-env/bin/activate

cd realtime
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload --log-level info
```

This starts the backend that provides live prediction data.

## 2. Run the live Streamlit app (separate terminal)

Open a new terminal window, activate the same environment, and run the live app:

```bash
cd wisdm-dataset
source wisdm-env/bin/activate

cd app
streamlit run app/live_app.py
```

This app visualizes the live Rush Index stream.

## 3. Run the explanatory Streamlit demo app

To run the app that explains the metrics and model behavior:

```bash
cd wisdm-dataset
source wisdm-env/bin/activate

cd app
streamlit run app/app.py
```

This version is intended for demonstration and explanation purposes.

## Notes

- The backend server must be running for the live app to function.

- Always run the backend and Streamlit apps in separate terminals.

- Large datasets are intentionally excluded from version control.

- Ensure that the paths are correct in all the app scripts and mobile app scripts.

- Ensure that the testing device is connected to the same network as the computer running the script + change IP address accordingly in RushRecorder.swift and server.py

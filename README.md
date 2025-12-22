# upk_rush_recorder

UPK

DEMO
cd /Users/pikakriznar/Documents/1_letnik_MAG/UPK/Projekti/Razpoznava_hitenja_projekt/data/wisdm+smartphone+and+smartwatch+activity+and+biometrics+dataset/wisdm-dataset
source wisdm-env/bin/activate
cd /Users/pikakriznar/Documents/1_letnik_MAG/UPK/Projekti/Razpoznava_hitenja_projekt/data/wisdm+smartphone+and+smartwatch+activity+and+biometrics+dataset/wisdm-dataset/realtime
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload --log-level info

V POSEBEJ ZAŽENEŠ live_app.py
cd /Users/pikakriznar/Documents/1_letnik_MAG/UPK/Projekti/Razpoznava_hitenja_projekt/data/wisdm+smartphone+and+smartwatch+activity+and+biometrics+dataset/wisdm-dataset
source wisdm-env/bin/activate
cd /Users/pikakriznar/Documents/1_letnik_MAG/UPK/Projekti/Razpoznava_hitenja_projekt/data/wisdm+smartphone+and+smartwatch+activity+and+biometrics+dataset/wisdm-dataset/app
streamlit run app/live_app.py


EXPLAINING APP DEMO
cd /Users/pikakriznar/Documents/1_letnik_MAG/UPK/Projekti/Razpoznava_hitenja_projekt/data/wisdm+smartphone+and+smartwatch+activity+and+biometrics+dataset/wisdm-dataset
source wisdm-env/bin/activate
cd /Users/pikakriznar/Documents/1_letnik_MAG/UPK/Projekti/Razpoznava_hitenja_projekt/data/wisdm+smartphone+and+smartwatch+activity+and+biometrics+dataset/wisdm-dataset/app
streamlit run app/app.py

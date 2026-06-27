# 台湾・澎湖 歴史地名天気 日本統治時代の台湾地名で現在の天気を見るStreamlit試作版です。

## ローカル起動

```powershell
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 公開する場合

Streamlit Community Cloudにこのフォルダを含むGitHubリポジトリを接続し、`streamlit_app.py`をエントリポイントにします。

## データ

- 地図形状: g0v/twgeojson由来のGeoJSON
- 天気: Open-Meteo Forecast API
- 音声: edge-tts

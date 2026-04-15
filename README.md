# EventScope

EventScope 是一個用 Streamlit 製作的金融事件模擬平台，支援：

- 全球重大事件資料庫
- 事件衝擊模擬
- 傳導路徑分析
- 投資組合壓力測試

## 本機啟動

先安裝套件：

```bash
pip install -r requirements.txt
```

前景模式啟動：

```bash
streamlit run app.py --server.port 8505
```

然後打開：

```text
http://localhost:8505
```

## 背景常駐啟動

啟動：

```bash
./start_app.sh
```

停止：

```bash
./stop_app.sh
```

預設 port 是 `8505`，背景模式會把 log 寫到 `streamlit.log`。

## 開機自動啟動

如果你希望這台 Mac 每次登入後都自動把網站打開，可以使用：

```bash
./install_launch_agent.sh
```

移除自動啟動：

```bash
./uninstall_launch_agent.sh
```

安裝後，EventScope 會由 macOS `launchd` 自動維持在背景執行，預設網址是：

```text
http://localhost:8505
```

## 分享給別人

如果你的電腦正在執行 app，對方可以試著開：

```text
http://你的外部 IP:8505
```

但這種方式有幾個限制：

- 你的電腦必須一直開著
- Streamlit 程式不能中斷
- 網路或防火牆不能擋住該 port

## 部署

這個專案已經包含：

- `.streamlit/config.toml`
- `render.yaml`
- `.gitignore`

可作為部署到 Streamlit Community Cloud 或 Render 的起點。

## 最推薦做法

如果你是要「穩定給別人開」，建議優先用 Render。

原因：

- 會有固定網址
- 不需要你的電腦一直開著
- 已經有 `render.yaml`

## 上線前一步

你還需要把這個資料夾放到 GitHub。

如果目前還沒建 repo，可以在專案目錄執行：

```bash
git init
git add .
git commit -m "Initial EventScope app"
```

然後建立 GitHub repo 後執行：

```bash
git branch -M main
git remote add origin <你的 GitHub repo 網址>
git push -u origin main
```

### Render

1. 把專案推到 GitHub
2. 登入 Render
3. 點 `New +`
4. 選 `Blueprint`
5. 選你的 GitHub repo
6. Render 會自動讀取 `render.yaml`
7. 按建立並等待部署完成
8. 完成後你會拿到固定網址，直接傳別人開

目前 `render.yaml` 已經設定好：

- 安裝：`pip install -r requirements.txt`
- 啟動：`streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

### Streamlit Community Cloud

1. 把專案推到 GitHub
2. 到 Streamlit Community Cloud 建立新 app
3. Main file path 設成 `app.py`
4. 部署

如果只是想快速展示，這個也可以，但我還是更推薦 Render。

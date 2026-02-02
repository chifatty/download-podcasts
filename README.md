# download-podcasts

這個 repo 提供一個 Python script，用來下載「豬探長推理故事集」的 EP 節目。

Podcast 連結：
https://open.firstory.me/user/detectivepig/episodes

注意：
- 該 podcast 不只有 EP，還有 SP「探長會客室」系列
- 這個 script 只會下載 EP（標題包含 EP.<number>）

## 使用方式（Poetry）

```bash
poetry install
poetry run python download_detectivepig_eps.py 111 113
```

參數：
- `start` / `end`：EP 起訖號
- `--out`：輸出資料夾（預設為 `~/Downloads`）
- `--overwrite`：覆蓋同名檔（`true/false`）

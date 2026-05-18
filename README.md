# download-podcasts

這個 repo 提供 Python script，用來下載 Firstory 上的 Podcast 節目。

## 安裝

```bash
poetry install
```

## 支援的 Podcast

### 豬探長推理故事集

Podcast 連結：https://open.firstory.me/user/detectivepig/episodes

注意：
- 該 podcast 不只有 EP，還有 SP「探長會客室」系列
- 這個 script 只會下載 EP（標題包含 EP.\<number\>）

```bash
poetry run python download_detectivepig_eps.py 111 113 --out=downloads
```

參數：
- `start` / `end`：EP 起訖號
- `--out`：輸出資料夾（預設為 `~/Downloads`）
- `--overwrite`：覆蓋同名檔（`true/false`）

---

### 打開小耳朵

Podcast 連結：https://open.firstory.me/user/littleears/episodes

注意：
- 集數沒有 EP 編號，需用關鍵字篩選

**列出所有集數：**
```bash
poetry run python download_littleears_eps.py list
```

**用關鍵字下載（符合任一關鍵字即下載）：**
```bash
# 先確認會比對到哪些集數
poetry run python download_littleears_eps.py search 北極熊 鯨鯊 --dry_run

# 正式下載
poetry run python download_littleears_eps.py search 北極熊 鯨鯊 --out=downloads
```

參數：
- `keywords`：一個或多個關鍵字（空格分隔），符合任一即下載
- `--out`：輸出資料夾（預設為 `downloads`）
- `--overwrite`：覆蓋同名檔（`true/false`）
- `--dry_run`：僅列出符合集數，不下載

---

### 任意 Firstory RSS（關鍵字篩選）

如果節目沒有固定 EP 編號，可以直接指定 RSS，像 `打開小耳朵` 一樣用標題關鍵字篩選。

你提供的 RSS：
`https://feed.firstory.me/rss/user/ckg2mhkljssl708756xu1zvcy`

**列出所有集數：**
```bash
poetry run python download_firstory_keyword_eps.py list --rss=https://feed.firstory.me/rss/user/ckg2mhkljssl708756xu1zvcy
```

**用關鍵字下載（符合任一關鍵字即下載）：**
```bash
# 先確認會比對到哪些集數
poetry run python download_firstory_keyword_eps.py search 關鍵字A 關鍵字B --rss=https://feed.firstory.me/rss/user/ckg2mhkljssl708756xu1zvcy --dry_run

# 正式下載
poetry run python download_firstory_keyword_eps.py search 關鍵字A 關鍵字B --rss=https://feed.firstory.me/rss/user/ckg2mhkljssl708756xu1zvcy --out=downloads
```

參數：
- `keywords`：一個或多個關鍵字（空格分隔），符合任一即下載
- `--rss`：Firstory RSS feed URL
- `--out`：輸出資料夾（預設為 `downloads`）
- `--overwrite`：覆蓋同名檔（`true/false`）
- `--dry_run`：僅列出符合集數，不下載

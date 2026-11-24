# api_go → api（Rust）Migration 總結

把 `api_go/`（Go）轉成 Rust，放在 `api/`。`api_go/` 沒有任何改動。

## 驗證狀態

| 項目 | 結果 |
|---|---|
| `cargo build` | ✅ 無警告 |
| `cargo clippy --all-targets` | ✅ 無警告 |
| `cargo test` | ✅ 22 個測試全部通過 |
| 真實環境端到端測試 | ❌ **尚未執行**：沒有 MongoDB、AWS 憑證和 `mongodb.properties`，沒有實際連過 Mongo 或 Rekognition |

> 正式切換前，請在實際環境跑一次完整的上傳和 feedback 流程。

測試範圍：

- **純函式：**
  - 空 payload 和一般 payload 的 JSON 格式
  - Rekognition 比對結果的過濾與去重
  - ISO 週次 key 格式
  - `$push` 的欄位名稱
  - `ox` 白名單
  - `file` 路徑檢查
  - 「上一週」key 跨年計算
  - properties 檔解析
- **Handler 層（用 `tower::ServiceExt::oneshot` 直接打 router）：**
  - GET 請求
  - 非 multipart 的上傳
  - 缺少 `upload` 欄位
  - 不合法的 JSON
  - 超過 2MB 的 feedback body
  - `ox` 不在白名單（例如 `$set`）
  - `file` 路徑穿越（例如 `../../etc/passwd`）

  以上都確認回 200、帶正確 header、內容是空 payload。

## 參考資料

- [rust-classes：Migration from Go](https://rust-classes.com/chapter_migration_from_go)：照著它的建議用 tokio、`Cargo.toml`、`pub`、`async`/`await`。這篇沒講 HTTP、JSON、Mongo 和錯誤處理，所以這幾塊的套件是另外選的。
- [aws-sdk-rekognition](https://docs.rs/aws-sdk-rekognition/latest/aws_sdk_rekognition/)：參數型別直接對照 1.126.0 原始碼確認：
  - `face_match_threshold` 是 `f32`
  - `max_faces` 是 `i32`
  - 圖片用 `Blob`
  - `similarity()` 回傳 `Option<f32>`

## 檔案對應

| Go | Rust |
|---|---|
| `api_go/main.go` | `api/src/main.rs` |
| `api_go/db/mongodb.go` | `api/src/db.rs` |
| `api_go/aws/rekognition.go` | `api/src/aws.rs` |

## 套件與寫法對應

| Go | Rust |
|---|---|
| `net/http` | `axum` + `tokio` |
| `panic` + `defer recover()` | 回傳 `anyhow::Result`；出錯就記 log，回 200 和空 payload |
| `encoding/json` | `serde` / `serde_json` |
| `gopkg.in/mgo.v2` | 官方 `mongodb` 3.x |
| `aws-sdk-go` | `aws-sdk-rekognition` + `aws-config` |
| `github.com/google/uuid` | `uuid` |
| `time`（日期、ISO 週） | `chrono` |
| `magiconair/properties` | 自己寫的簡易 `key=value` 解析 |
| `fmt.Println` / `log` | `tracing` + `tracing-subscriber` |

## 跟 Go 版維持一致的行為

- **JSON 欄位：** 欄位名稱和順序跟 Go 一樣：
  - payload：`Count`、`File`、`Data`
  - 每筆比對結果：`Id`、`Name`、`Img`、`Similarity`
  - `Similarity` 是小數兩位的**字串**
- **空 payload：** 內容一字不差是 `{"Count":0,"File":"","Data":null}`。Go 的 nil slice 會輸出 `null`，所以 Rust 用 `Option<Vec<Face>>` 來對應。
- **出錯時的回應：** 以下情況一律回 200，帶 `Access-Control-Allow-Origin: *` 和 `Content-Type: application/json`，內容是空 payload：
  - 不是 POST
  - 不是 multipart
  - 缺少 `upload` 欄位
  - JSON 不合法
  - body 太大
  - 呼叫 Mongo 或 AWS 失敗
- **路由：** 用 `any()` 接受所有 HTTP method，再自己檢查是不是 POST，不讓 axum 自動回 405、415、400、413。
- **feedback body：** 不看 `Content-Type`，直接把 body 當 JSON 解析，跟 Go 的 `json.NewDecoder(r.Body)` 一樣。
- **Rekognition 比對規則：**
  - 送出時 threshold 是 `0.2`，本機再過濾 `>= 20`
  - 最相似的那張低於 20 就當作沒找到
  - 依 `ExternalImageId` 去重，最多回 2 筆
  - 回傳結果缺少 `ExternalImageId` 或 `Similarity` 時當作錯誤處理（Go 版在這裡會因 nil pointer panic）
- **上傳流程：**
  - 圖片先存到 `/var/www/like-av.xyz/images/<YYYY-MM-DD>/<uuid前8碼>_<檔名>`，才去查 Mongo
  - 沒有比對結果時不存檔
  - 建日期目錄只建一層，錯誤忽略，同 Go 的 `os.Mkdir`
  - 查不到女優資料時回空 payload
- **feedback 流程：**
  - 缺少的欄位視為 `""`（但 `ox` 和 `file` 會再經過下方的檢查）
  - 只有 `ox == "like"` 時才把臉加進 Rekognition 索引（IndexFaces）
  - 成功時回 200、body 是空的
- **週次 key：** 用本地時間的 ISO 年 + ISO 週，不補零，例如 `"20263"`。
- **MongoDB 連線：**
  - 從工作目錄讀 `mongodb.properties`，檔案不存在就無法啟動
  - 連 `localhost:27017`
  - 資料庫和驗證來源都是 `dark`
- **監聽位址：** `0.0.0.0:9090`。

## 刻意改掉的地方

| 項目 | Go | Rust |
|---|---|---|
| AWS / Mongo 連線 | AWS session 每個請求重建 | 啟動時建立一次，之後共用 |
| 上傳大小 | `ParseMultipartForm(32 << 20)`，超過的部分寫到暫存檔 | `DefaultBodyLimit` 設為 32MB（axum 預設只有 2MB） |
| 啟動檢查 | `mgo.DialWithInfo` 連不上就 panic | 啟動時 `ping` Mongo，失敗就停止 |
| feedback JSON | 寬鬆 | 比較嚴格，後面多帶資料或傳 `null` 都算錯 |
| 上傳檔名 | `filepath.Base` | `Path::file_name`；檔名是 `..` 時直接當成錯誤 |
| 相似度精度 | `float64` | SDK 給的是 `f32`；格式化到小數兩位時，極少數邊界值可能差 0.01 |

## Go 版原本就有的問題（Rust 版已修復）

這三項是**刻意和 Go 版不同**的行為。

### 1. 路徑穿越（`/feedback` 的 `file` 欄位）

- **問題：** Go 版把 `file` 直接接在 `IMAGES_ROOT` 後面。傳 `../../etc/passwd` 這類值，就能讀到圖片目錄以外的檔案，再送去 Rekognition。
- **修法：** `validate_image_path`（`src/main.rs`）要求 `file` 和 `/upload` 回傳的格式完全一致：`YYYY-MM-DD/<8 個 hex>_<檔名>`。
  - 日期必須是合法日期，而且要補零（例如 `2026-1-1` 不行）。
  - 檔名部分不能包含 `/`、`\` 或 NUL。

  這樣路徑只會有「一層日期目錄 + 一個檔名」，`../`、絕對路徑、多層目錄都會被擋下。
- **範圍：** 不管 `ox` 是 `like` 還是 `unlike` 都會檢查，因為 `file` 也會寫進 Mongo。
- **失敗時：** 回空 payload，不讀檔、不呼叫 AWS、不寫 DB。

### 2. `$push` 欄位名稱由前端決定（`ox` 欄位）

- **問題：** Go 版直接拿前端傳來的 `ox` 當 `$push` 的欄位名稱，任何人都能往 `actress` 文件裡塞任意陣列欄位。
- **修法：** 新增 `db::Vote` enum（`src/db.rs`），只接受 `"like"` 和 `"unlike"`。`upsert_one_feedback` 改成吃 `Vote`，所以型別上就不可能把任意字串當成欄位名稱。
- **失敗時：** 其他值（包括 `""`、`"dislike"`、`"Like"`、`"$set"`）一律回空 payload，不寫 DB。

> ⚠️ **相容性：** 前端如果送的是 `like` / `unlike` 以外的值，例如 `dislike`，feedback 會開始失敗。切換前請確認前端實際送出的值。

### 3. 「上一週」在第 1 週算錯（`aggregate_week_rank`）

- **問題：** Go 版用「ISO 週數減 1」，所以在第 1 週會算出 `"<年>0"`，而不是去年的最後一週。
- **修法：** 新增 `last_week_key`，改成「今天往前推 7 天，再取那天的 ISO 年 + ISO 週」，跨年也正確。例如 2027-01-04（2027-W01）的上一週是 `"202653"`。
- **注意：** 週次 key 的格式沒變（不補零），所以既有資料不受影響。這個函式目前仍然沒有 handler 呼叫。

## 執行方式

```bash
cd api
# 1. 工作目錄放 mongodb.properties
#    username=...
#    password=...
# 2. 準備 AWS 憑證（環境變數、~/.aws 或 IAM role 都可以）
cargo run --release   # 監聽 0.0.0.0:9090

cargo test            # 執行測試
```

### Log

預設只印 `api` 自己的 INFO 以上，其他套件（AWS SDK、mongodb、hyper 等）只印 WARN 以上。每個請求大約一行：

```
INFO api: upload file="2026-11-24/xxxxxxxx_a.jpg" faces="<id>:<name>:94.28, <id>:<name>:92.54"
INFO api: upload: no match file_name="a.jpg"
WARN api: upload: actress not found id="<id>"
INFO api: feedback id="<id>" ox="unlike" file="2026-11-24/xxxxxxxx_a.jpg"
ERROR api: <錯誤原因>          # 任何回空 payload 的錯誤
```

需要更多細節時用 `RUST_LOG` 調整：

```bash
RUST_LOG=api=debug ./api   # 加上 Rekognition 比對筆數、request id
RUST_LOG=debug ./api       # 全部套件的 debug（非常多）
```

> **注意：** `aws_config` 在 INFO 等級會印出 AWS access key ID。預設設定已經把它擋掉，不要在正式環境開 `RUST_LOG=info`。

## 編譯 Linux amd64 binary

```bash
cd api
./build-linux-amd64.sh   # 產出 target/linux-amd64/api
```

- **建置方式：** 在 `rust:1-alpine`（linux/amd64）容器裡編譯，target 是 `x86_64-unknown-linux-musl`。
- **產出：** static-pie 靜態連結，**不依賴伺服器的 glibc 版本**。已在 Alpine 3 和 Debian bookworm（x86_64）的容器實際執行過。
- **TLS：** 用 rustls，沒有 OpenSSL 依賴。唯一的 C 依賴 `aws-lc-sys` 會在容器內編譯。
- **必須裝 `linux-headers`：** `aws-lc-sys` 編譯時如果找不到 `<linux/random.h>`，就只會用 `getentropy()` 取亂數，沒有備援。
  - **症狀：** 在 kernel < 3.17（沒有 `getrandom` 系統呼叫）的機器上，一啟動就印出 `getentropy failed.` 然後 abort。
  - **裝了之後：** 改走 `urandom.c`，`getrandom` 不能用時會退回讀 `/dev/urandom`。
  - **注意：** 腳本已經裝了。如果改過建置環境，要先清掉 `api-cargo-target` volume（`docker volume rm api-cargo-target`），因為 aws-lc-sys 不會自動重新偵測標頭檔。
- **原始碼怎麼進容器：** 用 tar 串流，不用 bind mount。macOS 隱私權限會擋 Docker 讀 `~/Documents`。
- **編譯時間：** 在 Apple Silicon 上要用 amd64 模擬，第一次約 9 分鐘。之後 crate 和編譯快取都留在 Docker volume（`api-cargo-registry`、`api-cargo-target`），會快很多。
- **檔案大小：** `Cargo.toml` 的 `[profile.release]` 設了 `strip = true`，會拿掉 symbol 和 debug info，檔案從約 34MB 縮到約 23MB。代價是 panic 的 backtrace 不會顯示函式名稱。

## MongoDB 升級（舊版 → mongo:7）

### 為什麼要升級

第一次在伺服器上啟動 Rust 版時，出現這個錯誤：

```
Error: failed to connect to MongoDB
  Kind: Server selection timeout ... Error: Kind: I/O error: unexpected end of file
```

- **錯誤的意思：** TCP 有連上，但伺服器在握手時直接關掉連線。
- **原因：** Rust 官方 driver `mongodb` 3.10 的 `DRIVER_MIN_WIRE_VERSION = 9`，也就是**最低需要 MongoDB 4.4**。舊容器 `local-mongo` 用的是約 9 年前的 `mongo` image（3.x 年代），看不懂新版 driver 的 OP_MSG 協定。
- **Go 版為什麼能用：** `mgo.v2` 用的是舊版的 OP_QUERY 協定。
- **誤導性的標籤：** 錯誤裡的 `SystemOverloadedError` 只是 driver 給網路錯誤加的標籤，不代表伺服器過載。

資料量很小（`actress` 1090 筆、`rank` 423 筆），所以採用 **dump → 新容器 → restore**，不在原地一版一版升（3.x → 3.6 → 4.0 → 4.2 → 4.4）。新容器直接沿用 27017，Rust 程式碼不用改。

### 步驟

以下在伺服器上 `api` 目錄（放 `mongodb.properties` 的地方）執行。

**0. 讀取帳密、確認 CPU 支援 AVX**

```bash
U=$(sed -n 's/^[[:space:]]*username[[:space:]]*[=:][[:space:]]*//p' mongodb.properties)
P=$(sed -n 's/^[[:space:]]*password[[:space:]]*[=:][[:space:]]*//p' mongodb.properties)

grep -o -m1 avx /proc/cpuinfo || echo "NO AVX"
```

- **AVX：** MongoDB 5.0 以上在 x86_64 需要 AVX。如果印出 `NO AVX`，下面的 `mongo:7` 改成 `mongo:4.4`（driver 支援的最低版本），`mongosh` 改成 `mongo`。
- **帳密從檔案讀：** 直接從 `mongodb.properties` 讀，避免手打。`docker exec` 會原封不動傳參數，密碼有特殊字元也沒問題。

**1. 從舊容器 dump**

```bash
docker exec local-mongo mongodump -u "$U" -p "$P" \
  --authenticationDatabase dark -d dark -o /tmp/dump
docker cp local-mongo:/tmp/dump ./dump
```

- **驗證資料庫是 `dark`：** 跟 Go 版 `mgo.DialInfo` 的預設一樣。
- **出現 `Authentication failed`：** 通常是帳密被 shell 吃掉，例如手打時 `$`、`!` 沒加引號。改用上面從檔案讀的方式。

**2. 停掉舊容器（保留，方便退回）**

```bash
docker update --restart=no local-mongo   # 避免重開機後又自動起來搶 27017
docker stop local-mongo
```

**3. 啟動 mongo:7**

```bash
read -s -p "root password: " ROOT_PW; echo

docker run -d --name mongo7 --restart unless-stopped \
  -p 127.0.0.1:27017:27017 \
  -v mongo7-data:/data/db \
  -e MONGO_INITDB_ROOT_USERNAME=root \
  -e MONGO_INITDB_ROOT_PASSWORD="$ROOT_PW" \
  mongo:7
```

- **只綁 `127.0.0.1`：** 不要把 MongoDB 對外開放。API 和 DB 在同一台機器，綁本機就夠了。
- **新的 root 帳號：** 跟 app 用的帳密分開。
- **出現 `missing signature key`：** 代表伺服器上的 Docker 太舊，看不懂 Docker Hub 現在的 OCI image index 格式。兩種解法：
  - **升級 Docker（建議）：** 會重啟 daemon，同機其他容器會短暫中斷。
  - **在其他機器 pull 後傳過來：**
    ```bash
    docker pull --platform linux/amd64 mongo:7
    docker save --platform linux/amd64 mongo:7 | gzip > mongo7.tar.gz
    # 傳到伺服器後
    gunzip -c mongo7.tar.gz | docker load
    ```
    如果舊版 Docker 啟動時出現 `pthread_create failed: Operation not permitted`，原因是舊的 seccomp 設定擋掉了 `clone3`。可以加 `--security-opt seccomp=unconfined` 繞過，但會關掉一層隔離。

**4. 在 `dark` 建立 app 使用者（沿用 properties 的帳密）**

```bash
sleep 5   # 等 mongod 起來
docker exec -e U="$U" -e P="$P" mongo7 mongosh -u root -p "$ROOT_PW" \
  --authenticationDatabase admin --quiet --eval \
  'db.getSiblingDB("dark").createUser({user: process.env.U, pwd: process.env.P, roles: [{role: "readWrite", db: "dark"}]})'
```

**5. Restore 並核對**

```bash
docker cp ./dump mongo7:/tmp/dump
docker exec mongo7 mongorestore -u "$U" -p "$P" --authenticationDatabase dark \
  --nsInclude 'dark.*' /tmp/dump

docker exec mongo7 mongosh -u "$U" -p "$P" --authenticationDatabase dark dark --quiet \
  --eval 'print(db.actress.countDocuments(), db.rank.countDocuments())'
```

- **實際結果：** 1513 筆全部還原（1090 + 423），0 筆失敗。
- **索引：** unique 索引 `actress.id_1`、`rank.week_1` 也一起還原了。
- **如果卡在建索引：** 3.x 的舊索引設定有時新版不接受。加 `--noIndexRestore` 重跑，再手動建上面兩個 unique 索引。

**6. 確認歷史資料用過哪些 `ox` 值（驗證白名單）**

```bash
docker exec mongo7 mongosh -u "$U" -p "$P" --authenticationDatabase dark dark --quiet --eval '
db.actress.aggregate([
  {$project: {k: {$objectToArray: "$$ROOT"}}},
  {$unwind: "$k"},
  {$group: {_id: "$k.k", n: {$sum: 1}}},
  {$sort: {n: -1}}
]).forEach(printjson)'
```

正常只會有 `_id`、`id`、`name`、`img`、`count`、`like`、`unlike`。出現其他欄位名（例如 `dislike`）就要調整 `db::Vote` 白名單。

**7. 啟動 Rust 版並測試**

```bash
./api   # 應看到 listening on 0.0.0.0:9090

# /upload：只讀 DB，並存一張圖到 images 目錄
curl -s -F "upload=@/path/to/face.jpg" http://localhost:9090/upload
```

`/feedback` 會寫入正式資料，測之前要注意：
- **`unlike`：** `count` +1、在 `unlike` 陣列加一筆，並在本週 `rank` 加一票。
- **`like`：** 除了上面這些，還會把圖加進 Rekognition 的正式 collection `rankingcollection`。

### 退回

```bash
docker stop mongo7 && docker start local-mongo
```

**注意：** 舊容器停掉期間，Go 版 API 連不到 Mongo。

## 切換前檢查清單

- [x] **MongoDB 版本：** 原本的版本太舊，Rust driver 不支援，已升級到 mongo:7 並完成 restore（見「MongoDB 升級」）。
- [ ] **`ox` 欄位清單：** 跑「MongoDB 升級」第 6 步，確認歷史資料只有 `like` / `unlike`。
- [ ] **端到端測試：** 在實際環境跑一次 `/upload` 和 `/feedback`，確認 Rekognition 和 Mongo 的讀寫都正常。
- [ ] **前端相容性：** 確認前端拿到的 JSON 格式和以前一樣。
- [x] **release 設定：** 已加 `strip = true`。
- [ ] **進一步縮小（可選）：** rust-classes 建議的 `opt-level = "z"`、`lto = true` 目前**沒有**加。`opt-level = "z"` 是用效能換大小，這個服務不需要。`lto = true` 會讓編譯時間明顯變長（模擬 amd64 時尤其明顯）。
- [ ] **確認前端的 `ox` 值：** 確認前端只送 `like` / `unlike`。
- [ ] **確認前端的 `file` 值：** 確認前端送回的 `file` 就是 `/upload` 回傳的 `File`，格式為 `YYYY-MM-DD/<8 hex>_<檔名>`。

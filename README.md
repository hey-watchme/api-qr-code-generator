# WatchMe QR Code Generator API

デバイス共有用のQRコードを生成・管理するAPIです。

## ✅ 開発状況

**開発完了・本番稼働中** (2025-12-06)

### 完了した対応

**✅ 専用S3バケット`watchme-qrcodes`を新規作成**

1. **S3バケット設定**:
   - バケット名: `watchme-qrcodes`
   - リージョン: `ap-southeast-2` (Sydney)
   - Block Public Access: **無効** (QRコードは公開アクセス可能)
   - ACL: 有効（`public-read`で公開）
   - バケットポリシー: 全ユーザーがGetObjectアクセス可能

2. **IAM権限設定完了**:
   - `watchme-api-user`に以下の権限を付与
   - `s3:PutObject`, `s3:PutObjectAcl`, `s3:GetObject`, `s3:DeleteObject`, `s3:ListBucket`

3. **環境変数更新完了**:
   - EC2: `/home/ubuntu/watchme-api-qr-code-generator/.env` → `S3_BUCKET_NAME=watchme-qrcodes`
   - GitHub Actions Secrets: `S3_BUCKET_NAME=watchme-qrcodes`

4. **API実装変更完了**:
   - Presigned URL方式を削除（7日間有効期限問題を解決）
   - `ACL='public-read'`で永続的な公開URLを生成
   - 公開URL形式: `https://watchme-qrcodes.s3.ap-southeast-2.amazonaws.com/devices/{device_id}/qrcode.png`

5. **iOS実装完了**:
   - QRCodeService.swift作成
   - DeviceEditViewにQRコード表示UI追加
   - 自動生成・表示機能実装済み

### 動作確認済み

- ✅ API呼び出し成功
- ✅ QRコード画像生成・S3アップロード成功
- ✅ 公開アクセス確認済み（HTTP 200）
- ✅ iOSアプリでのQRコード表示成功

---

## 📋 概要

このAPIは、WatchMeプラットフォームでデバイスを共有するためのQRコードを生成します。
生成されたQRコードはAWS S3に保存され、SupabaseデータベースのURLが記録されます。

### 主な機能

- デバイスIDからQRコード画像を生成
- AWS S3への自動アップロード
- Supabaseデータベースとの自動連携（qr_code_url更新）
- QRコードの削除機能

### 技術スタック

- **FastAPI** - Webフレームワーク
- **AWS S3** - 画像ストレージ（リージョン: ap-southeast-2）
- **Supabase** - データベース
- **qrcode** - QRコード生成ライブラリ
- **Pillow** - 画像処理
- **Boto3** - AWS SDK

---

## 🚀 デプロイプロセス

### 前提条件
- AWS ECRリポジトリ: `754724220380.dkr.ecr.ap-southeast-2.amazonaws.com/watchme-qr-code-generator`
- EC2インスタンス: `3.24.16.82`
- ポート: `8020`
- SSH鍵: `/Users/kaya.matsumoto/watchme-key.pem`

### デプロイフロー

```
┌─────────────────┐
│  ローカル環境    │
└────────┬────────┘
         │
         │ 1. コード変更時のみ
         ▼
   ./deploy-ecr.sh ─────► ECRにイメージをプッシュ
                          (754724220380.dkr.ecr...watchme-qr-code-generator:latest)
                                    │
                                    │
                                    ▼
┌─────────────────────────────────────┐
│  EC2サーバー (3.24.16.82)            │
│                                     │
│  2. サービス再起動                    │
│  sudo systemctl restart             │
│    watchme-qr-code-generator        │
│         │                           │
│         ▼                           │
│  run-qr-code-generator.sh           │
│    - ECRから最新イメージをPULL       │
│    - 環境変数を読み込み              │
│    - コンテナを起動                  │
└─────────────────────────────────────┘
```

### Step 1: ローカルでコード変更（コード変更時のみ）

```bash
cd /Users/kaya.matsumoto/projects/watchme/api/qr-code-generator

# ECRにDockerイメージをプッシュ
./deploy-ecr.sh
```

**このステップが行うこと：**
1. ECRにログイン
2. `Dockerfile.prod`を使ってイメージをビルド
3. イメージにタグ付け（`latest`とタイムスタンプ）
4. ECRにプッシュ

### Step 2: EC2でサービス再起動

```bash
# EC2にSSH接続
ssh -i /Users/kaya.matsumoto/watchme-key.pem ubuntu@3.24.16.82

# サービスを再起動（推奨）
sudo systemctl restart watchme-qr-code-generator

# または、手動でスクリプトを実行
./watchme-qr-code-generator/run-qr-code-generator.sh
```

---

## ⚙️ 環境設定

### 環境変数ファイル（EC2: `/home/ubuntu/.env.qr-code-generator`）

```env
# Supabase Configuration
SUPABASE_URL=https://qvtlwotzuzbavrzqhyvt.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
S3_BUCKET_NAME=watchme-avatars
AWS_REGION=ap-southeast-2

# API Configuration
API_PORT=8020
API_HOST=0.0.0.0
```

### 重要な設定項目

| 項目 | 値 | 説明 |
|-----|-----|------|
| S3バケット名 | `watchme-qrcodes` | QRコード専用バケット |
| AWSリージョン | `ap-southeast-2` | シドニー |
| ポート | `8021` | EC2内部ポート |

---

## 🗺️ ルーティング詳細

| 項目 | 値 | 説明 |
|------|-----|------|
| **🏷️ サービス名** | QR Code Generator API | デバイス共有用QRコード生成 |
| **📊 役割** | QRコード管理 | デバイスID → QRコード画像 → S3保存 |
| | | |
| **🌐 外部アクセス（Nginx）** | | |
| └ 公開エンドポイント | `https://api.hey-watch.me/qrcode/` | 外部からのアクセスパス |
| └ Nginx設定ファイル | `/etc/nginx/sites-available/api.hey-watch.me` | |
| └ proxy_pass先 | `http://localhost:8021/` | 内部転送先 |
| └ タイムアウト | 60秒 | read/connect/send |
| | | |
| **🔌 API内部エンドポイント** | | |
| └ ヘルスチェック | `/health` | GET |
| └ **QRコード生成** | `/v1/devices/{device_id}/qrcode` | POST - QR生成・S3保存 |
| └ **QRコード削除** | `/v1/devices/{device_id}/qrcode` | DELETE |
| | | |
| **🐳 Docker/コンテナ** | | |
| └ コンテナ名 | `watchme-api-qr-code-generator` | ✅ 統一命名規則 |
| └ ポート（内部） | 8021 | コンテナ内 |
| └ ポート（公開） | `127.0.0.1:8021:8021` | ローカルホストのみ |
| └ ネットワーク | `watchme-network` | 固定IP: 172.27.0.20 |
| └ ヘルスチェック | `/health` | Docker healthcheck |
| | | |
| **☁️ AWS ECR** | | |
| └ リポジトリ名 | `watchme-api-qr-code-generator` | ✅ ECRリポジトリ |
| └ リージョン | ap-southeast-2 (Sydney) | |
| └ URI | `754724220380.dkr.ecr.ap-southeast-2.amazonaws.com/watchme-api-qr-code-generator:latest` | |
| | | |
| **⚙️ 起動管理** | | |
| └ 起動スクリプト | `run-prod.sh` | docker-compose管理 |
| └ 起動コマンド | `docker-compose -f docker-compose.prod.yml up -d` | |
| | | |
| **📂 ディレクトリ** | | |
| └ ソースコード | `/Users/kaya.matsumoto/projects/watchme/api/qr-code-generator` | ローカル |
| └ GitHubリポジトリ | `hey-watchme/api-qr-code-generator` | |
| └ EC2配置場所 | `/home/ubuntu/watchme-api-qr-code-generator` | 本番実行ディレクトリ |
| | | |
| **🔗 呼び出し元（想定）** | | |
| └ iOSアプリ | デバイス登録時・詳細画面 | 自動生成・表示 |
| └ 呼び出しURL | `https://api.hey-watch.me/qrcode/v1/devices/{device_id}/qrcode` | フルパス |
| | | |
| **📥 データソース** | | |
| └ 入力テーブル | `devices` | デバイスID検証 |
| └ 出力先（S3） | `watchme-qrcodes/devices/{device_id}/qrcode.png` | QRコード画像 |
| └ 出力テーブル | `devices.qr_code_url` | S3 URL保存 |

---

## 📡 APIエンドポイント

### ヘルスチェック
```
GET /health
```

### QRコード生成

#### 生成/更新
```
POST /v1/devices/{device_id}/qrcode
```
- **認証**: 現在無効（開発・テスト用）
- **処理内容**:
  1. デバイスIDの検証（devicesテーブルに存在するか確認）
  2. QRコード画像生成（512x512px PNG）
  3. S3にアップロード
  4. データベース更新（devices.qr_code_url）
- **レスポンス**:
  ```json
  {
    "qrCodeUrl": "https://watchme-qrcodes.s3.ap-southeast-2.amazonaws.com/devices/{device_id}/qrcode.png"
  }
  ```

#### 削除
```
DELETE /v1/devices/{device_id}/qrcode
```

### アクセスURL

| 用途 | URL |
|-----|-----|
| **内部アクセス** | `http://localhost:8020/` |
| **外部アクセス** | `https://api.hey-watch.me/qrcode/` |

---

## 🗄️ データベース設計

### SQL Migration

```sql
-- Add qr_code_url column to devices table
ALTER TABLE devices
ADD COLUMN IF NOT EXISTS qr_code_url TEXT;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_devices_qr_code_url ON devices(qr_code_url);

-- Add comment
COMMENT ON COLUMN devices.qr_code_url IS 'S3 URL of the QR code image for device sharing';
```

**実行方法**:
1. Supabaseダッシュボードにアクセス
2. SQL Editorを開く
3. `migration.sql`の内容を実行

---

## 📁 S3バケット構造

```
watchme-qrcodes/
└── devices/
    └── {device_id}/
        └── qrcode.png
```

**注意**: アバター画像は別バケット(`watchme-avatars`)で管理されています。

---

## 🔍 トラブルシューティング

### サービスが起動しない

```bash
# ログを確認
sudo journalctl -u watchme-qr-code-generator -n 100 --no-pager

# コンテナのログを確認
docker logs watchme-qr-code-generator --tail 50
```

### 環境変数が読み込まれない

```bash
# コンテナ内の環境変数を確認
docker exec watchme-qr-code-generator env | grep -E '^AWS_|^S3_'

# 期待される出力:
# AWS_ACCESS_KEY_ID=AKIA...
# AWS_SECRET_ACCESS_KEY=...
# S3_BUCKET_NAME=watchme-avatars
# AWS_REGION=ap-southeast-2
```

### S3アップロードエラー

**原因**:
1. 環境変数が読み込まれていない
2. AWSアクセスキーが無効
3. バケット名が間違っている

**確認手順**:
```bash
# 環境変数を確認
docker exec watchme-qr-code-generator env | grep S3_BUCKET_NAME
# 出力: S3_BUCKET_NAME=watchme-avatars であること
```

---

## 🧪 テスト

### ローカルテスト（開発中）

```bash
# 仮想環境作成（初回のみ）
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# .envファイル作成
cp .env.example .env
# .envファイルを編集して環境変数を設定

# アプリ起動
python3 app.py
```

### 本番環境テスト

```bash
# ヘルスチェック
curl https://api.hey-watch.me/qrcode/health

# QRコード生成テスト
curl -X POST https://api.hey-watch.me/qrcode/v1/devices/{device_id}/qrcode

# レスポンス例:
# {"qrCodeUrl":"https://watchme-qrcodes.s3.ap-southeast-2.amazonaws.com/devices/{device_id}/qrcode.png"}
```

---

## 📝 開発時の注意事項

1. **UUID形式**: device_idは必ずUUID形式
2. **QRコード内容**: デバイスID（UUID）のみをエンコード
3. **画像形式**: PNG（512x512px）
4. **エンドポイントパス**: `/v1/`プレフィックスが必要
5. **アトミック性**: S3アップロード後のDB更新失敗時は自動ロールバック

---

## 🔗 関連ドキュメント

- [avatar-uploader API](../avatar-uploader/README.md) - アバター管理API（参考実装）
- [Server Configs README](../../server-configs/README.md) - サーバー全体の構成

---

## 📊 QRコード仕様

| 項目 | 値 |
|-----|-----|
| **フォーマット** | PNG |
| **サイズ** | 512x512px |
| **エンコード内容** | デバイスID（UUID） |
| **エラー訂正レベル** | L（Low） |
| **ボックスサイズ** | 10px |
| **ボーダー** | 2ボックス |
| **色** | 黒/白 |

---

## 🚧 今後の拡張予定

- [ ] 認証機能の有効化（JWTトークン検証）
- [ ] QRコードのカスタマイズ機能（ロゴ埋め込み、カラー変更）
- [ ] バッチ生成API（複数デバイスの一括生成）
- [ ] キャッシュ機能（既存QRコードの再利用）

---

## 📝 変更履歴

### 2025-12-06: 本番稼働開始

- ✅ 専用S3バケット`watchme-qrcodes`作成・設定完了
- ✅ IAM権限設定完了（`s3:PutObjectAcl`追加）
- ✅ Presigned URL方式を削除、`ACL='public-read'`で永続URL生成に変更
- ✅ iOS実装完了（QRCodeService、DeviceEditView）
- ✅ 動作確認完了

# CXO Dashboard (金融機関向け・プロトタイプ)

金融機関のCEO / CIO / CISO / CRO / CFO 等（CXO）が「自室で素早く状況把握する」ことを想定したダッシュボードのプロトタイプです。

まずは **Python + Streamlit** で立ち上げ、KPI・アラート・市場/流動性・システム健全性などを素早く追加できる土台を作ります。

## 目的（プロトタイプの方針）

- **一画面で把握**: 重要KPI / 重要アラート / 直近変化を最小操作で確認
- **説明可能**: 指標の定義・更新時刻・根拠を追える（後続でデータ出所リンクを追加）
- **安全側**: 本番データ接続は後回しにし、まずはUI・情報設計を固める

## 必要要件

- Python 3.9+

## セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 起動

プロジェクト直下から実行してください。

```bash
.venv/bin/streamlit run app/Home.py
```

ブラウザで http://localhost:8501 を開きます。すでに起動中の場合は、コード変更後に一度停止してから再起動してください。

## ディレクトリ

- `app/` Streamlitアプリ
- `app/pages/` 画面（後で増やす）
- `app/lib/` モデル・ダミーデータ・共通UI

## 次に入れていく想定（例）

- データソース: DB / API / S3 / Snowflake / Databricks 等
- 認証認可: SSO（SAML/OIDC）, RBAC（CXOロール別ビュー）
- 監査: アクセスログ、重要操作ログ、ダッシュボード表示内容のスナップショット


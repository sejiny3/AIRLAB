#!/bin/bash
# Serve the fine-tuned π0.5 from Colab through a quick tunnel (train_pi05.ipynb cell 7).
# Every stage prints and has a time limit, so a stall says where it is.
DRIVE=${DRIVE:-/content/drive/MyDrive/airlab_pi05}
VERSION=2026.10.4
SHA256=ae5e8add7884b0531d66bbca4570d1de491ff6da51e4ebe7eb160cdf241d9e42
LOAD_LIMIT=900
TUNNEL_LIMIT=60

cd /content/openpi || exit 1
CKPT=$(ls -d /content/checkpoints/pi05_airlab/run1/[0-9]* "$DRIVE"/checkpoints/pi05_airlab/run1/[0-9]* 2>/dev/null | grep -E '/[0-9]+$' | head -1)
if [ -z "$CKPT" ]; then
  echo "체크포인트를 찾지 못했습니다. 1번 칸을 실행했는지 확인하세요."
  exit 1
fi
echo "체크포인트: $CKPT"

# 앞서 중지한 칸의 서버가 남아 있으면 GPU와 포트를 차지합니다
pkill -f serve_pi05.py
pkill -f 'cloudflared tunnel'

if [ ! -x /content/cloudflared ]; then
  echo "터널 프로그램을 받는 중입니다"
  curl -fsSL --connect-timeout 20 --max-time 180 --retry 2 -o /content/cloudflared.part \
    "https://github.com/cloudflare/cloudflared/releases/download/$VERSION/cloudflared-linux-amd64" \
    || { echo "터널 프로그램을 받지 못했습니다. 이 칸을 다시 실행하세요."; exit 1; }
  echo "$SHA256  /content/cloudflared.part" | sha256sum -c --quiet || exit 1
  chmod +x /content/cloudflared.part
  mv /content/cloudflared.part /content/cloudflared
fi

XLA_PYTHON_CLIENT_MEM_FRACTION=0.6 PYTHONUNBUFFERED=1 .venv/bin/python /content/AIRLAB/pi05/serve_pi05.py \
  --checkpoint "$CKPT" > /content/serve.log 2>&1 &
SERVER=$!
trap 'kill $SERVER $TUNNEL 2> /dev/null' EXIT

echo "모델을 올리는 중입니다"
SECONDS=0
NEXT=60
until curl -sf -m 5 localhost:8000/healthz > /dev/null; do
  kill -0 $SERVER 2> /dev/null || { echo "서버가 멈췄습니다:"; tail -20 /content/serve.log; exit 1; }
  if [ $SECONDS -ge $LOAD_LIMIT ]; then
    echo "$((LOAD_LIMIT / 60))분이 지나도 준비되지 않아 중단합니다:"
    tail -20 /content/serve.log
    exit 1
  fi
  if [ $SECONDS -ge $NEXT ]; then
    echo "$((SECONDS / 60))분 경과, 마지막 로그: $(tail -1 /content/serve.log | cut -c1-120)"
    NEXT=$((NEXT + 60))
  fi
  sleep 3
done
echo "모델 준비 완료 ($SECONDS초)"

echo "터널을 여는 중입니다"
/content/cloudflared tunnel --no-autoupdate --url http://localhost:8000 > /content/tunnel.log 2>&1 &
TUNNEL=$!
SECONDS=0
until URL=$(grep -oE 'https://[-a-z0-9]+\.trycloudflare\.com' /content/tunnel.log | grep -v '//api\.' | head -1); [ -n "$URL" ]; do
  if ! kill -0 $TUNNEL 2> /dev/null || [ $SECONDS -ge $TUNNEL_LIMIT ]; then
    echo "터널을 열지 못했습니다:"
    tail -5 /content/tunnel.log | cut -c1-200
    exit 1
  fi
  sleep 1
done
echo "대시보드에 넣을 서버 주소: $URL"

wait $TUNNEL
echo "터널이 닫혔습니다:"
tail -5 /content/tunnel.log | cut -c1-200

#!/bin/bash
# Claude API 키를 확인한 뒤 ~/.unbolt_key 에 저장한다 (키는 화면에 표시되지 않는다).
#   bash ~/unbolt/workshop/setup/setup_api_key.sh
set -e
echo "Anthropic Console(https://console.anthropic.com)에서 만든 API 키를 붙여넣고 Enter."
echo "(입력해도 화면에 아무것도 보이지 않는 것이 정상입니다)"
read -rs -p "API 키: " key; echo
key="$(echo "$key" | tr -d '[:space:]')"
[[ "$key" == sk-ant-* ]] || { echo "✘ sk-ant- 로 시작하는 키가 아닙니다."; exit 1; }

# 저장하기 전에 확인: 요금이 들지 않는 모델 목록 호출
ANTHROPIC_API_KEY="$key" python3 - <<'EOF' || exit 1
import anthropic
try:
    page = anthropic.Anthropic().models.list(limit=1)
    print("✔ API 연결 확인:", page.data[0].id if page.data else "ok")
except anthropic.AuthenticationError:
    raise SystemExit("✘ 키가 올바르지 않습니다 (401). Console에서 키를 다시 확인하세요. 저장하지 않았습니다.")
except anthropic.APIConnectionError as e:
    raise SystemExit(f"✘ 연결 실패: {e.__cause__ or e}\n  → pip3 install --user --upgrade Brotli 후 다시 시도. 저장하지 않았습니다.")
EOF

umask 077
printf 'export ANTHROPIC_API_KEY=%q\n' "$key" > ~/.unbolt_key
chmod 600 ~/.unbolt_key
echo "✔ ~/.unbolt_key 에 저장 (${#key}자, 본인만 읽기 가능)"
grep -q unbolt_key ~/.bashrc || echo '[ -f ~/.unbolt_key ] && source ~/.unbolt_key' >> ~/.bashrc
echo "새 터미널부터 적용됩니다 (지금 터미널은: source ~/.unbolt_key)"

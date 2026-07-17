#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${PROJECT_ROOT}/web/frontend"
PUBLIC_PORT=8888
BACKEND_PORT=8000
CONDA_ENV=knowledge-base
CONDA_COMMAND="${CONDA_EXE:-conda}"

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  trap - EXIT INT TERM

  for pid in "${FRONTEND_PID}" "${BACKEND_PID}"; do
    if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
      kill "${pid}" 2>/dev/null || true
    fi
  done

  for pid in "${FRONTEND_PID}" "${BACKEND_PID}"; do
    if [[ -n "${pid}" ]]; then
      wait "${pid}" 2>/dev/null || true
    fi
  done
}

fail() {
  echo "启动失败：$*" >&2
  exit 1
}

port_is_listening() {
  local port="$1"
  command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1
}

wait_for_url() {
  local name="$1"
  local url="$2"
  local pid="$3"
  local attempt

  for attempt in {1..60}; do
    if ! kill -0 "${pid}" 2>/dev/null; then
      return 1
    fi
    if curl --silent --fail --output /dev/null "${url}"; then
      return 0
    fi
    sleep 0.25
  done

  echo "${name}在等待时间内没有就绪：${url}" >&2
  return 1
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

cd "${PROJECT_ROOT}"

command -v "${CONDA_COMMAND}" >/dev/null 2>&1 || fail "未找到 conda，请先安装并初始化 Conda"
command -v npm >/dev/null 2>&1 || fail "未找到 npm，请先安装 Node.js"
command -v curl >/dev/null 2>&1 || fail "未找到 curl"
[[ -d "${FRONTEND_DIR}/node_modules" ]] || fail "前端依赖未安装，请先执行：npm --prefix web/frontend install"

if port_is_listening "${PUBLIC_PORT}"; then
  fail "端口 ${PUBLIC_PORT} 已被占用"
fi
if port_is_listening "${BACKEND_PORT}"; then
  fail "后端内部端口 ${BACKEND_PORT} 已被占用"
fi

echo "正在启动后端（内部地址：http://127.0.0.1:${BACKEND_PORT}）..."
"${CONDA_COMMAND}" run --no-capture-output -n "${CONDA_ENV}" \
  python -m uvicorn backend.main:app \
  --reload --reload-dir "${PROJECT_ROOT}/backend" \
  --host 127.0.0.1 --port "${BACKEND_PORT}" &
BACKEND_PID=$!

wait_for_url "后端" "http://127.0.0.1:${BACKEND_PORT}/api/health" "${BACKEND_PID}" \
  || fail "后端启动失败，请查看上方日志"

echo "正在启动前端..."
npm --prefix "${FRONTEND_DIR}" run dev -- \
  --host 127.0.0.1 --port "${PUBLIC_PORT}" --strictPort &
FRONTEND_PID=$!

wait_for_url "前端" "http://127.0.0.1:${PUBLIC_PORT}" "${FRONTEND_PID}" \
  || fail "前端启动失败，请查看上方日志"

echo
echo "前后端已启动：http://127.0.0.1:${PUBLIC_PORT}"
echo "API 文档：http://127.0.0.1:${PUBLIC_PORT}/api/docs"
echo "按 Ctrl+C 停止全部服务。"

while kill -0 "${BACKEND_PID}" 2>/dev/null && kill -0 "${FRONTEND_PID}" 2>/dev/null; do
  sleep 1
done

if ! kill -0 "${BACKEND_PID}" 2>/dev/null; then
  wait "${BACKEND_PID}" || status=$?
  fail "后端进程已退出（状态码：${status:-0}）"
fi

wait "${FRONTEND_PID}" || status=$?
fail "前端进程已退出（状态码：${status:-0}）"

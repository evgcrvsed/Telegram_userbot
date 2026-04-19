from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse
from pathlib import Path
import json
import re  # для очистки ввода

from config.settings import Settings
from infrastructure.repositories.json_icon_repository import JsonIconRepository

app = FastAPI(title="Icons Editor", version="1.2")

settings = Settings()
FILE_PATH = Path(settings.ICONS_JSON_PATH)
LOGO_DIR = Path("data/logoUrl")
REPO = JsonIconRepository(settings)


HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <title>Icons Editor</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    <style>
        ol li { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
        .logo-img {
            width: 42px;
            height: 42px;
            object-fit: contain;
            background-color: #27272a;
            border-radius: 8px;
            padding: 2px;
        }
        .emoji-input { font-size: 1.5rem; }
    </style>
</head>
<body class="bg-zinc-950 text-zinc-100 min-h-screen p-8">
    <div class="max-w-4xl mx-auto">
        <div class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-4xl font-bold flex items-center gap-3">
                    <i class="fas fa-icons text-emerald-500"></i>
                    Icons Editor
                </h1>
                <p class="text-zinc-400 mt-1">Управление эмодзи и логотипами команд (только цифры)</p>
            </div>
            <div class="flex gap-3">
                <button onclick="toggleSort()" id="sort-btn"
                        class="px-6 py-2.5 bg-zinc-800 hover:bg-zinc-700 rounded-xl flex items-center gap-2">
                    <i class="fas fa-sort"></i>
                    <span>Пустые снизу</span>
                </button>
                <button onclick="saveAll()" 
                        class="px-8 py-2.5 bg-emerald-600 hover:bg-emerald-500 rounded-xl font-medium flex items-center gap-2">
                    <i class="fas fa-save"></i>
                    <span>Сохранить всё</span>
                </button>
            </div>
        </div>

        <ol id="icon-list" class="space-y-3"></ol>
    </div>

    <script>
        let items = [];
        let emptyFirst = false;
        const PASSWORD = "admin123";   // ←←← Тот же пароль, что и в бэкенде (можно вынести в .env позже)

        function getLogoUrl(teamName) {
            const encoded = encodeURIComponent(teamName);
            return `/static/logos/${encoded}.png`;
        }

        function render() {
            const ol = document.getElementById('icon-list');
            ol.innerHTML = items.map(i => {
                const logoUrl = getLogoUrl(i.key);
                return `
                    <li data-key="${i.key}" class="flex items-center gap-4 bg-zinc-900 hover:bg-zinc-800 p-5 rounded-3xl group">
                        <img src="${logoUrl}" 
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                             class="logo-img">
                        <div class="w-10 h-10 bg-zinc-800 rounded-xl hidden items-center justify-center text-zinc-500 text-xl font-mono">
                            ?
                        </div>

                        <span class="font-mono text-sm text-zinc-300 w-56 truncate">${i.key}</span>

                        <input id="input-${i.key}" 
                               value="${i.emoji || ''}" 
                               class="emoji-input flex-1 bg-zinc-800 text-white px-6 py-3.5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-emerald-500 text-center"
                               maxlength="20"
                               oninput="this.value = this.value.replace(/[^0-9]/g, '')">   <!-- Только цифры на клиенте -->

                        <button onclick="save('${i.key}')" 
                                class="px-8 py-3 bg-emerald-600 hover:bg-emerald-500 rounded-2xl text-sm font-medium transition-all active:scale-95">
                            Сохранить
                        </button>
                    </li>
                `;
            }).join('');
        }

        function toggleSort() {
            emptyFirst = !emptyFirst;
            const btn = document.getElementById('sort-btn');
            btn.innerHTML = emptyFirst 
                ? `<i class="fas fa-sort"></i><span>Пустые сверху</span>` 
                : `<i class="fas fa-sort"></i><span>Пустые снизу</span>`;

            items.sort((a, b) => {
                const aEmpty = !a.emoji;
                const bEmpty = !b.emoji;
                if (aEmpty === bEmpty) return 0;
                return emptyFirst ? (aEmpty ? -1 : 1) : (aEmpty ? 1 : -1);
            });
            render();
        }

        async function save(key) {
            const input = document.getElementById(`input-${key}`);
            let value = input.value.trim();

            // Дополнительная очистка на клиенте
            value = value.replace(/[^0-9]/g, '');

            const btn = event.currentTarget;
            const originalHTML = btn.innerHTML;
            btn.innerHTML = 'Сохраняем...';
            btn.disabled = true;

            try {
                const res = await fetch(`/icons/${encodeURIComponent(key)}?emoji=${encodeURIComponent(value)}&password=${encodeURIComponent(PASSWORD)}`, {
                    method: 'POST'
                });

                if (res.ok) {
                    const item = items.find(i => i.key === key);
                    if (item) item.emoji = value;
                    showToast('✅ Сохранено', 'success');
                } else if (res.status === 401) {
                    showToast('❌ Неверный пароль', 'error');
                } else {
                    showToast('❌ Ошибка сохранения', 'error');
                }
            } catch (e) {
                showToast('❌ Ошибка соединения', 'error');
            }

            setTimeout(() => {
                btn.innerHTML = originalHTML;
                btn.disabled = false;
            }, 800);
        }

        async function saveAll() {
            const btn = document.querySelector('button[onclick="saveAll()"]');
            const originalHTML = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Сохраняем...';
            btn.disabled = true;

            let count = 0;
            for (let i of items) {
                let emoji = document.getElementById(`input-${i.key}`).value.trim();
                emoji = emoji.replace(/[^0-9]/g, '');   // Только цифры

                if (emoji !== i.emoji) {
                    try {
                        await fetch(`/icons/${encodeURIComponent(i.key)}?emoji=${encodeURIComponent(emoji)}&password=${encodeURIComponent(PASSWORD)}`, { 
                            method: 'POST' 
                        });
                        i.emoji = emoji;
                        count++;
                    } catch (e) {}
                }
            }

            btn.innerHTML = originalHTML;
            btn.disabled = false;
            showToast(`✅ Сохранено ${count} изменений`, 'success');
        }

        function showToast(message, type = 'success') {
            const toast = document.createElement('div');
            toast.className = `fixed bottom-8 right-8 px-6 py-4 rounded-2xl shadow-2xl text-sm font-medium z-50 ${
                type === 'success' ? 'bg-emerald-600' : 'bg-red-600'
            }`;
            toast.textContent = message;
            document.body.appendChild(toast);

            setTimeout(() => {
                toast.style.transition = 'opacity 0.3s';
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }, 2800);
        }

        async function load() {
            try {
                const res = await fetch('/icons/data');
                items = await res.json();
                items.forEach(i => { if (!i.emoji) i.emoji = ''; });
                toggleSort();
            } catch (e) {
                console.error("Ошибка загрузки:", e);
            }
        }

        load();
    </script>
</body>
</html>
'''


@app.get("/icons", response_class=HTMLResponse)
async def get_icons():
    return HTML_TEMPLATE


@app.get("/icons/data")
async def get_icons_data():
    try:
        data = REPO.get_data()
        return [{"key": k, "emoji": v.get("emoji", "")} for k, v in data.items()]
    except Exception:
        raise HTTPException(status_code=500, detail="Ошибка чтения данных")


@app.post("/icons/{key}")
async def update_emoji(
        key: str,
        emoji: str = Query(...),
):
    # Очистка: оставляем только цифры
    cleaned = re.sub(r'[^0-9]', '', emoji.strip())

    try:
        REPO.save_emoji(key, cleaned)
        return {"status": "ok", "saved_value": cleaned}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Статические файлы — логотипы
from fastapi.staticfiles import StaticFiles
import os

os.makedirs("data/logoUrl", exist_ok=True)
app.mount("/static/logos", StaticFiles(directory="data/logoUrl"), name="logos")
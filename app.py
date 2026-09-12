from flask import Flask, request, jsonify, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = "yhsh_board_final.db"
ADMIN_PASS = "f7839"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- 前台：乾淨的留言瀏覽區 + 彈出式投稿視窗 ---
INDEX_HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>幼華中學 匿名交流版</title>
    <style>
        :root {
            --bg: #f8fafc;
            --card: #ffffff;
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --text-main: #0f172a;
            --text-sub: #64748b;
            --border: #e2e8f0;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: var(--bg); color: var(--text-main); display: flex; justify-content: center; padding: 40px 16px; }
        .container { width: 100%; max-width: 650px; }
        
        /* 頂部 Header */
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }
        .title-area h1 { font-size: 1.5rem; font-weight: 700; }
        .title-area p { color: var(--text-sub); font-size: 0.85rem; margin-top: 4px; }
        .btn-post-open { background: var(--primary); color: #fff; border: none; padding: 10px 18px; border-radius: 20px; font-weight: 600; font-size: 0.9rem; cursor: pointer; transition: 0.2s; box-shadow: 0 2px 4px rgba(37,99,235,0.2); }
        .btn-post-open:hover { background: var(--primary-hover); transform: translateY(-1px); }

        /* 貼文卡片 */
        .post-card { background: var(--card); border-radius: 12px; padding: 18px 20px; border: 1px solid var(--border); margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }
        .post-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .post-author { font-weight: 600; font-size: 0.95rem; color: var(--primary); }
        .post-date { font-size: 0.8rem; color: var(--text-sub); }
        .post-content { font-size: 0.95rem; line-height: 1.6; white-space: pre-wrap; word-break: break-all; }

        /* 彈出式投稿視窗 (Modal) */
        .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.4); display: none; justify-content: center; align-items: center; padding: 16px; z-index: 99; backdrop-filter: blur(2px); }
        .modal-box { background: var(--card); width: 100%; max-width: 500px; border-radius: 16px; padding: 24px; border: 1px solid var(--border); box-shadow: 0 10px 25px rgba(0,0,0,0.1); position: relative; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
        .modal-header h3 { font-size: 1.2rem; font-weight: 700; }
        .close-btn { background: none; border: none; font-size: 1.4rem; color: var(--text-sub); cursor: pointer; line-height: 1; }
        
        .input-group { margin-bottom: 16px; }
        label { display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 6px; color: var(--text-sub); }
        input, textarea { width: 100%; border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; font-size: 0.95rem; outline: none; background: #fafafa; }
        input:focus, textarea:focus { border-color: var(--primary); background: #fff; }
        textarea { height: 100px; resize: none; }
        
        .submit-btn { width: 100%; background: var(--primary); color: #fff; border: none; padding: 12px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 0.95rem; }
        .submit-btn:hover { background: var(--primary-hover); }
        #status-msg { margin-top: 10px; font-size: 0.85rem; text-align: center; }

        .admin-footer { text-align: center; margin-top: 40px; font-size: 0.8rem; }
        .admin-footer a { color: var(--text-sub); text-decoration: none; }
    </style>
</head>
<body>
<div class="container">
    <header>
        <div class="title-area">
            <h1>幼華中學 匿名版</h1>
            <p>校園心情交流專區</p>
        </div>
        <button class="btn-post-open" onclick="openModal()">✍️ 我要投稿</button>
    </header>

    <!-- 留言列表區 -->
    <div id="posts-container"></div>

    <div class="admin-footer">
        <a href="/admin">🔒 版主審核通道</a>
    </div>
</div>

<!-- 投稿彈跳視窗 -->
<div class="modal-overlay" id="postModal">
    <div class="modal-box">
        <div class="modal-header">
            <h3>📝 匿名投稿</h3>
            <button class="close-btn" onclick="closeModal()">×</button>
        </div>
        <div class="input-group">
            <label>匿名暱稱</label>
            <input type="text" id="nickname" placeholder="例如：操場的小貓（留空預設為匿名同學）" maxlength="15">
        </div>
        <div class="input-group">
            <label>想說的話</label>
            <textarea id="content" placeholder="分享有趣的事情或心情...（經版主審核後公開）" maxlength="300"></textarea>
        </div>
        <button class="submit-btn" onclick="submitPost()">確認送出投稿</button>
        <div id="status-msg"></div>
    </div>
</div>

<script>
    function openModal() {
        document.getElementById('postModal').style.display = 'flex';
        document.getElementById('status-msg').innerText = '';
    }
    function closeModal() {
        document.getElementById('postModal').style.display = 'none';
    }

    async function loadPublicPosts() {
        const res = await fetch('/api/public_posts');
        const posts = await res.json();
        const container = document.getElementById('posts-container');
        container.innerHTML = posts.length ? '' : '<p style="text-align:center;color:#64748b;padding:40px 0;font-size:0.95rem;">目前還沒有公開的留言，點右上角搶頭香！</p>';
        posts.forEach(p => {
            container.innerHTML += `
                <div class="post-card">
                    <div class="post-header">
                        <span class="post-author"># ${p.nickname}</span>
                        <span class="post-date">${p.created_at}</span>
                    </div>
                    <div class="post-content">${p.content}</div>
                </div>
            `;
        });
    }

    async function submitPost() {
        const nickname = document.getElementById('nickname').value.trim() || '匿名同學';
        const content = document.getElementById('content').value.trim();
        const msg = document.getElementById('status-msg');

        if (!content) {
            msg.style.color = '#ef4444';
            msg.innerText = '請填寫內容！';
            return;
        }

        const res = await fetch('/api/submit_post', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nickname, content })
        });

        if (res.ok) {
            msg.style.color = '#10b981';
            msg.innerText = '✅ 投稿成功！等待版主審核通過就會顯示在版面上。';
            document.getElementById('content').value = '';
            setTimeout(closeModal, 1500);
        } else {
            msg.style.color = '#ef4444';
            msg.innerText = '投稿失敗，請稍後再試。';
        }
    }

    loadPublicPosts();
</script>
</body>
</html>
"""

# --- 後台：版主登入（具備顯示/隱藏密碼）與審核 ---
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>版主審核後台 - 幼華中學</title>
    <style>
        :root { --bg: #f1f5f9; --card: #ffffff; --primary: #0f172a; --text: #0f172a; --border: #cbd5e1; }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
        body { background: var(--bg); color: var(--text); padding: 40px 16px; display: flex; justify-content: center; }
        .container { width: 100%; max-width: 650px; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
        .card { background: var(--card); border-radius: 12px; padding: 18px; margin-bottom: 12px; border: 1px solid var(--border); box-shadow: 0 2px 4px rgba(0,0,0,0.03); }
        .actions { margin-top: 12px; display: flex; gap: 8px; }
        .btn { padding: 8px 14px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 600; }
        .btn-approve { background: #10b981; color: #fff; }
        .btn-delete { background: #ef4444; color: #fff; }
        
        .login-box { background: var(--card); padding: 24px; border-radius: 12px; border: 1px solid var(--border); max-width: 400px; margin: 0 auto; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
        
        /* 密碼輸入框與眼睛按鈕包裹層 */
        .password-wrapper { position: relative; display: flex; align-items: center; margin-bottom: 16px; }
        .password-wrapper input { width: 100%; padding: 10px 42px 10px 12px; border: 1px solid var(--border); border-radius: 6px; outline: none; font-size: 0.95rem; }
        .password-wrapper input:focus { border-color: #2563eb; }
        .toggle-pwd-btn { position: absolute; right: 10px; background: none; border: none; cursor: pointer; font-size: 1.1rem; color: #64748b; padding: 4px; }
    </style>
</head>
<body>
<div class="container">
    <header>
        <h2>幼華中學 審核後台</h2>
        <a href="/" style="font-size: 0.9rem; text-decoration: none; color: #2563eb;">← 回留言板</a>
    </header>

    <div id="login-section" class="login-box">
        <label style="display:block;margin-bottom:8px;font-weight:600;font-size:0.9rem;">請輸入審核密碼：</label>
        <div class="password-wrapper">
            <input type="password" id="admin-pwd" placeholder="審核通行碼">
            <button type="button" class="toggle-pwd-btn" onclick="togglePasswordVisibility()" title="顯示/隱藏密碼">👁️</button>
        </div>
        <button class="btn" style="background:#2563eb;color:#fff;width:100%;padding:10px;" onclick="login()">驗證登入</button>
        <p id="err" style="color:#ef4444;font-size:0.85rem;margin-top:10px;text-align:center;"></p>
    </div>

    <div id="review-section" style="display:none;">
        <h4 style="margin-bottom:16px;">待審核投稿清單：</h4>
        <div id="review-list"></div>
    </div>
</div>

<script>
    let currentPassword = '';

    // 切換顯示/隱藏密碼功能
    function togglePasswordVisibility() {
        const pwdInput = document.getElementById('admin-pwd');
        const toggleBtn = event.currentTarget;
        if (pwdInput.type === 'password') {
            pwdInput.type = 'text';
            toggleBtn.innerText = '🙈';
        } else {
            pwdInput.type = 'password';
            toggleBtn.innerText = '👁️';
        }
    }

    async function login() {
        const pwd = document.getElementById('admin-pwd').value.trim();
        const res = await fetch('/api/admin/pending', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: pwd })
        });
        if (res.ok) {
            currentPassword = pwd;
            document.getElementById('login-section').style.display = 'none';
            document.getElementById('review-section').style.display = 'block';
            loadPendingList();
        } else {
            document.getElementById('err').innerText = '密碼錯誤，拒絕存取！';
        }
    }

    async function loadPendingList() {
        const res = await fetch('/api/admin/pending', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: currentPassword })
        });
        const posts = await res.json();
        const list = document.getElementById('review-list');
        list.innerHTML = posts.length ? '' : '<p style="color:#64748b;text-align:center;padding:30px 0;">目前沒有待審核的投稿！</p>';
        posts.forEach(p => {
            list.innerHTML += `
                <div class="card" id="post-${p.id}">
                    <div style="font-size:0.85rem;color:#64748b;margin-bottom:6px;"># ${p.nickname} · ${p.created_at}</div>
                    <div style="font-size:0.95rem;line-height:1.5;">${p.content}</div>
                    <div class="actions">
                        <button class="btn btn-approve" onclick="handleAction(${p.id}, 'approve')">✔ 審核通過（發布）</button>
                        <button class="btn btn-delete" onclick="handleAction(${p.id}, 'delete')">✖ 駁回刪除</button>
                    </div>
                </div>
            `;
        });
    }

    async function handleAction(id, action) {
        await fetch('/api/admin/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id, action, password: currentPassword })
        });
        document.getElementById(`post-${id}`).remove();
    }
</script>
</body>
</html>
"""

# --- 後端 API 路由 ---
@app.route('/')
def home():
    return render_template_string(INDEX_HTML)

@app.route('/admin')
def admin_page():
    return render_template_string(ADMIN_HTML)

@app.route('/api/public_posts', methods=['GET'])
def get_public_posts():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nickname, content, created_at FROM posts WHERE status = 1 ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([{"nickname": r[0], "content": r[1], "created_at": r[2]} for r in rows])

@app.route('/api/submit_post', methods=['POST'])
def submit_post():
    data = request.json or {}
    nickname = data.get('nickname', '匿名同學').strip()
    content = data.get('content', '').strip()
    if not content:
        return jsonify({"error": "內容不能為空"}), 400

    now = datetime.now().strftime("%m/%d %H:%M")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO posts (nickname, content, created_at, status) VALUES (?, ?, ?, 0)", (nickname, content, now))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/admin/pending', methods=['POST'])
def get_pending():
    data = request.json or {}
    pwd = (data.get('password') or '').strip()
    if pwd != ADMIN_PASS:
        return jsonify({"error": "密碼錯誤"}), 403

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nickname, content, created_at FROM posts WHERE status = 0 ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([{"id": r[0], "nickname": r[1], "content": r[2], "created_at": r[3]} for r in rows])

@app.route('/api/admin/action', methods=['POST'])
def admin_action():
    data = request.json or {}
    pwd = (data.get('password') or '').strip()
    if pwd != ADMIN_PASS:
        return jsonify({"error": "密碼錯誤"}), 403

    post_id = data.get('id')
    action = data.get('action')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if action == 'approve':
        cursor.execute("UPDATE posts SET status = 1 WHERE id = ?", (post_id,))
    elif action == 'delete':
        cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

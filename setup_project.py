import os

project_name = "myproject"

# ファイルリスト（フォルダ構造を含む）
file_paths = [
    "app/main.py",
    "app/core/config.py",
    "app/database.py",
    "app/models/user_model.py",
    "app/schemas/user_schema.py",
    "app/controllers/auth_controller.py",
    "app/views/auth_view.py",
    "app/templates/login.html",
    "app/templates/dashboard.html",
    "app/static/css/style.css",
    "requirements.txt",
    ".env"
]

def create_structure():
    for relative_path in file_paths:
        path = os.path.join(project_name, relative_path)

        # 必要なディレクトリを先に作成（ファイル部分を除いたパス）
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # 中身付きでファイルを作成
        with open(path, 'w', encoding='utf-8') as f:
            if path.endswith(".py"):
                f.write(f"# {os.path.basename(path)} : 自動生成されたモジュール\n")
                f.write("# このファイルに対応する処理を記述してください。\n\n")
            elif path.endswith(".html"):
                f.write(f"<!-- {os.path.basename(path)} : 自動生成されたHTMLテンプレート -->\n")
            elif path.endswith(".css"):
                f.write("/* style.css : カスタムスタイルをここに記述 */\n")
            elif path.endswith("requirements.txt"):
                f.write("fastapi\nuvicorn\njinja2\npython-dotenv\n")
            elif path.endswith(".env"):
                f.write("# .env : 環境変数をここに記述\n")

    print(f"✅ '{project_name}' プロジェクト構成を作成しました！")

if __name__ == "__main__":
    create_structure()
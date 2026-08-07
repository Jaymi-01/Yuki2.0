import sys
from yuki_app import YukiApp

if __name__ == "__main__":
    app = YukiApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)

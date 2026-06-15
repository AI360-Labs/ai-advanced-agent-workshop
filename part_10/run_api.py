"""Start the FastAPI server. Run from any directory: uv run python run_api.py"""

import uvicorn


def main() -> None:
    uvicorn.run(
        "api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()

from setuptools import setup, find_packages

setup(
    name="ai-data-agent",
    version="1.0.0",
    description="Conversational AI Data Analysis Platform",
    author="Your Name",
    author_email="vikas@bulba.app",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-multipart==0.0.6",
        "pandas==2.1.3",
        "openpyxl==3.1.2",
        "sqlalchemy==2.0.23",
        "pymysql==1.1.0",
        "python-dotenv==1.0.0",
        "pydantic==2.5.0",
        "numpy==1.26.2",
        "scikit-learn==1.3.2",
        "ollama==0.3.3",
        "aiofiles==23.2.1",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
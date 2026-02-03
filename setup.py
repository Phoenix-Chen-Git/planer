"""Setup configuration for Daily Planner & Logger."""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="daily-planner-logger",
    version="1.0.0",
    description="AI-powered daily planning and logging tool with DeepSeek",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Phoenix Chen",
    url="https://github.com/Phoenix-Chen-Git/planer",
    packages=find_packages(),
    py_modules=['daily', 'plan', 'check', 'summarize', 'feedback', 'calendar_view', 'web_server'],
    install_requires=[
        "openai>=1.0.0",
        "rich>=13.0.0",
        "python-dotenv>=1.0.0",
        "PyYAML>=6.0",
        "questionary>=2.0.0",
        "flask>=3.0.0",
    ],
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'daily=daily:main',
            'daily-web=web_server:main',
            'daily-plan=plan:main',
            'daily-check=check:main',
            'daily-summarize=summarize:main',
            'daily-feedback=feedback:main',
            'daily-calendar=calendar_view:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    include_package_data=True,
)

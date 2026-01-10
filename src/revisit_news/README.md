# pharmai

Summarize pharma news using AI

## Testing locally

```
cd src/revisit_news

# Create an .env file (Be sure to update the values)
cp .env.example .env

# Create a virtual environment (using venv module)
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip to the latest version (optional but recommended)
pip install --upgrade pip

# Install dependencies from requirements.txt
pip install -r requirements.txt

# Run locally
python3 local.py
```

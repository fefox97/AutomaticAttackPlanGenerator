FROM python:3.12

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py
ENV DEBUG=True

RUN mkdir /uploads

RUN apt update
RUN apt upgrade -y
RUN apt install -y nmap wkhtmltopdf fonts-noto-color-emoji

COPY . .

# install python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e ./sqlalchemy-utils

# gunicorn
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "run:app"]

FROM crpi-drioqgczr0409p0l.cn-beijing.personal.cr.aliyuncs.com/isdera/images:python3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "scrape.py"]

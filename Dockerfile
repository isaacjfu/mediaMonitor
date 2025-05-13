FROM crpi-drioqgczr0409p0l.cn-beijing.personal.cr.aliyuncs.com/isdera/images:python3.11

WORKDIR /app

COPY requirements.txt .
COPY packages/ /packages/
RUN pip install --no-index --find-links=/packages -r requirements.txt

COPY . .

CMD ["python", "scrape.py"]

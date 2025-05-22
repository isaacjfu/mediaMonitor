FROM crpi-drioqgczr0409p0l.cn-beijing.personal.cr.aliyuncs.com/isdera/images:python3.11

WORKDIR /app

RUN apt-get update && apt-get install -y \
    chromium chromium-driver \
    wget unzip \
    && apt-get clean

ENV CHROME_BIN=/usr/bin/chromium
ENV PATH="${PATH}:/usr/bin"

COPY requirements.txt .
COPY packages/ /packages/
RUN pip install --no-index --find-links=/packages -r requirements.txt


COPY . .

CMD ["python", "scrape.py"]

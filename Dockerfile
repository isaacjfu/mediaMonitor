FROM crpi-drioqgczr0409p0l.cn-beijing.personal.cr.aliyuncs.com/isdera/images:python3.11

# Install dependencies Chromium needs, and copying Chrome + setting path
RUN apt-get update && apt-get install -y \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libgbm1 libxcomposite1 libxdamage1 libxrandr2 \
    libasound2 libxss1 libxtst6 xdg-utils libu2f-udev \
    fonts-liberation libappindicator3-1 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*
COPY chrome/ /opt/chrome/
ENV PATH="/opt/chrome:${PATH}"
ENV CHROME_BIN=/opt/chrome/chrome

WORKDIR /app

COPY requirements.txt .
COPY packages/ /packages/
RUN pip install --no-index --find-links=/packages -r requirements.txt


COPY . .

CMD ["python", "scrape.py"]

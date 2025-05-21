# Python image is stored on Alibaba ACR
FROM crpi-drioqgczr0409p0l.cn-beijing.personal.cr.aliyuncs.com/isdera/images:python3.11

# Install dependencies Chromium needs, and copying Chrome + setting path
# Files are stored locally on ECS container. Following are libraries .deb packages needed
# RUN apt-get update && apt-get install -y \
#    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
#    libdrm2 libgbm1 libxcomposite1 libxdamage1 libxrandr2 \
#    libasound2 libxss1 libxtst6 xdg-utils libu2f-udev \
#    fonts-liberation libappindicator3-1 libgtk-3-0 \
#    && rm -rf /var/lib/apt/lists/*
COPY debs/ /debs/
RUN dpkg -i /debs/*.deb || apt-get -f install -y

# Set ENV path of chromium for selenium to use
COPY chrome/ /opt/chrome/
ENV PATH="/opt/chrome:${PATH}"
ENV CHROME_BIN=/opt/chrome/chrome

WORKDIR /app

# Pip packages are also stored locally on ECS container, as a wheel cache.
COPY requirements.txt .
COPY packages/ /packages/
RUN pip install --no-index --find-links=/packages -r requirements.txt


COPY . .

CMD ["python", "scrape.py"]

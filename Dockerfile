FROM python

RUN pip install update \
    && pip install pandas requests

COPY pull-data.py .
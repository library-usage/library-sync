FROM python:3.6
FROM jupyter/minimal-notebook

USER root

WORKDIR /app

ADD . /app

RUN pip install --trusted-host pypi.python.org -r requirements.txt
RUN conda install -y altair vega_datasets numpy pandas matplotlib requests

EXPOSE 8050

ENV NAME World

CMD ["python", "app.py"]


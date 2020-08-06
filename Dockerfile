FROM jupyter/minimal-notebook

RUN conda install -y altair vega_datasets numpy pandas matplotlib requests

CMD ["bin/bash"]
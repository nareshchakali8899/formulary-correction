FROM python:3.7

WORKDIR /app

COPY . /app

RUN pip install jupyter fuzzywuzzy tqdm nest_asyncio search-engine-parser wikipedia streamlit

EXPOSE 8501

ENTRYPOINT ["streamlit", "run"]

CMD ["app.py"]
# requirements 


from fastapi import FastAPI, Path, Body, HTTPException
from starlette.responses import Response
from pydantic import BaseModel
from typing import Optional
from sqlmodel import SQLModel, Field, Session, create_engine, select
from sqlalchemy import func
import os
import random
from dotenv import load_dotenv



app = FastAPI() 

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Quote API is running!!!!!!!!!!!!!"}

@app.head("/", include_in_schema=False)
def head_root():
    return Response(headers={"X-App-Status": "Alive"})


# database
load_dotenv()

database = create_engine(
    os.getenv("DATABASE_URL"),
    connect_args={"sslmode": "require"}
)



class Quote(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    author: str = Field(index=True, min_length=3, max_length=50)
    quote: str = Field(index=True, min_length=3, max_length=200)

class QuoteUpdate(SQLModel, table=False):
    author: Optional[str] = Field(default=None, min_length=3, max_length=50)
    quote: Optional[str] = Field(default=None, min_length=3, max_length=200)

SQLModel.metadata.create_all(database)

@app.post("/quotes")
def create_quote(
    quote: Quote = Body(
        ...,
        example={
            "author": "John Doe",
            "quote": "This is a quote"
        },
        description="Quote object to be created"
    )
):
    try:
        with Session(database) as session:
            session.add(quote)
            session.commit()
            session.refresh(quote) 
            print(quote.id)
            return f"Quote {quote.quote} by {quote.author} created successfully"
    except Exception as e:
        return {"error": str(e)}

@app.get("/quotes")
def get_quotes():
    try:
        with Session(database) as session:
            quotes = session.exec(select(Quote)).all()
            return quotes
    except Exception as e:
        return {"error": str(e)}

@app.get("/quotes/{quote_author}")
def get_quotes_by_author(quote_author: str):
    try:
        with Session(database) as session:
            quotes = session.exec(select(Quote).where(Quote.author.like(f"%{quote_author}%"))).all()
            if quotes == None:
                return {"error": f'{quote_author} not found'}
            return quotes
    except Exception as e:
        return {"error": str(e)}

@app.get("/random-quote/{quote_author}")
def get_random_quote(quote_author: str):
    try:
        with Session(database) as session:
            random_quote = session.exec(select(Quote).where(Quote.author.like(f"%{quote_author}%")).order_by(func.random()).limit(1)).first()
            if random_quote == None:
                return {"error": f'{quote_author} not found'}
            return random_quote
    except Exception as e:
        return {"error": str(e)}

@app.get("/random-quote")
def get_random_quote():
    with Session(database) as session:
        quotes = session.exec(select(Quote)).all()
        if not quotes:
            return {"error": "No quotes found"}
        return random.choice(quotes)

@app.put("/quotes/{quote_id}")
def update_quote(quote_id: int, quote: QuoteUpdate = Body(
    ...,
    example={
        "author": "John Doe",
        "quote": "This is a quote"
    }
)): 
    try:
        with Session(database) as session:
            quote_to_update = session.get(Quote, quote_id)
            if quote_to_update == None:
                return {"error": f'Quote with id {quote_id} not found'}
            quote_data = quote.model_dump(exclude_unset=True)
            for key, value in quote_data.items():
                setattr(quote_to_update, key, value)
            session.add(quote_to_update)
            session.commit()
            session.refresh(quote_to_update)
            return quote_to_update
    except Exception as e:
        return {"error": str(e)}

@app.delete("/quotes/{quote_author}/{quote_quote}")
def delete_quote(quote_author: str, quote_quote: str):
    try:
        with Session(database) as session:
            quote_to_delete = session.exec(select(Quote).where(Quote.author.like(f"%{quote_author}%"), Quote.quote.like(f"%{quote_quote}%"))).first()
            if quote_to_delete == None:
                return {"error": f'Quote with author {quote_author} and quote {quote_quote} not found'}
            session.delete(quote_to_delete)
            session.commit()
            return {"message": f'Quote with author {quote_author} and quote {quote_quote} deleted successfully'}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
# HNS Price API

A simple API to retrieve historical and current price data for Handshake (HNS).

## API Documentation

The full API documentation is available at [https://price.hns.dev/](https://price.hns.dev/).

## Endpoints

- `GET /latest`: Returns the single most recent price for a given currency.
- `GET /historical`: Returns stored price data with powerful filtering and aggregation.
- `GET /min`: Returns the minimum price for a given currency.
- `GET /max`: Returns the maximum price for a given currency.
- `GET /database`: Downloads the complete SQLite database file.

## Configuration

The application can be configured using a `.env` file. Create a `.env` file in the root of the project with the following variables:

- `COINGECKO_API_KEY`: Your CoinGecko API key. This is mandatory for fetching historical data.

Example `.env` file:
```
COINGECKO_API_KEY=your_api_key
```

## Running Locally

To run the project locally, you need to have Docker and Docker Compose installed.

1. Clone the repository:
   ```bash
   git clone https://github.com/falci-hns/hns-price-service.git
   cd hns-price-service
   ```

2. Run the application using Docker Compose:
   ```bash
   docker-compose up -d
   ```

The API will be available at `http://localhost:8000`.

## Ingesting Data

To ingest the latest price data, you can run the following command:
```bash
curl -X POST http://localhost:8000/ingest
```
This will fetch the latest price data from CoinGecko and store it in the local database.

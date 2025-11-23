# =========================
# 1️⃣ Frontend Build Stage
# =========================
FROM node:20 AS frontend-builder
WORKDIR /frontend
COPY weekly-planner/package*.json ./
RUN npm install
COPY weekly-planner/ .
RUN npm run build

# =========================
# 2️⃣ Backend Stage
# =========================
FROM python:3.13-slim AS backend
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY app ./app
COPY run.py config.py ./

# Copy built frontend into backend static folder
RUN mkdir -p app/static app/templates
COPY --from=frontend-builder /frontend/dist ./app/static

# Set environment variables
ENV PORT=8080
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Expose and run
EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "run:app"]

from fastapi import FastAPI

# Create FastAPI application instance
app = FastAPI(
    title="Quodsi API",
    description="Multi-tenant simulation platform API",
    version="0.1.0"
)

@app.get("/")
async def root():
    """Root endpoint for health checking"""
    return {
        "message": "Welcome to Quodsi API",
        "status": "running",
        "version": "0.1.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
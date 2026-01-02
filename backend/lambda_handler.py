from main import app  # import your FastAPI app
from mangum import Mangum

# Lambda handler
handler = Mangum(app)

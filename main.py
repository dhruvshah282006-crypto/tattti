from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pptx import Presentation
import shutil
import os

app = FastAPI()


def analyze_pptx(path):
    prs = Presentation(path)
    stats = {
        "slide_count": len(prs.slides),
        "word_count": 0,
        "image_count": 0,
        "chart_count": 0
    }

    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text:
                stats["word_count"] += len(shape.text.split())

            if shape.shape_type == 13:
                stats["image_count"] += 1

            if shape.shape_type == 3:
                stats["chart_count"] += 1

    return stats


def calculate_score(stats):
    if stats['slide_count'] < 5:
        return 0, "TOO_SHORT"

    score = 0
    score += stats['slide_count'] * 5
    score += stats['image_count'] * 10
    score += stats['chart_count'] * 20

    words_per_slide = stats['word_count'] / stats['slide_count']

    if words_per_slide > 60:
        score -= 20
    elif words_per_slide < 10:
        score -= 10

    return max(0, score), "READY"


@app.get("/")
def hello():
    return JSONResponse({"messsage": "backend is running!"})


@app.post("/score-ppt")
async def score_ppt(file: UploadFile = File(...)):
    try:
        temp_path = f"temp_{file.filename}"

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        stats = analyze_pptx(temp_path)
        score, flag = calculate_score(stats)

        os.remove(temp_path)

        return JSONResponse({
            "score": score,
            "status": flag,
            "stats": stats
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
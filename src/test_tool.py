from src.tools import get_area_metrics
import json

metrics = get_area_metrics(area_name="Dubai Marina", trans_group="Sales")
print(json.dumps(metrics, indent=2))
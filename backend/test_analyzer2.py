import pandas as pd
from app.services.statistical_analyzer import PandasAnalyzer

df = pd.DataFrame({'age': [20, 20]})
analyzer = PandasAnalyzer()
res = analyzer.descriptive_stats(df)
import json
print(json.dumps(res, indent=2))

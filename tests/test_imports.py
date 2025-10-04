import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from api.mexc_client import MexcClient
    print("✅ MexcClient imported successfully")
except ImportError as e:
    print(f"❌ MexcClient import failed: {e}")

try:
    from ai.analysis_engine import AIAnalysisEngine
    print("✅ AIAnalysisEngine imported successfully") 
except ImportError as e:
    print(f"❌ AIAnalysisEngine import failed: {e}")
try:
    from langchain.output_parsers import PydanticOutputParser
    print("✅ Found in langchain.output_parsers")
except ImportError:
    print("❌ Not found in langchain.output_parsers")

try:
    from langchain_core.output_parsers import PydanticOutputParser
    print("✅ Found in langchain_core.output_parsers")
except ImportError:
    print("❌ Not found in langchain_core.output_parsers")

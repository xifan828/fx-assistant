from pydantic import BaseModel

def basemodel_to_md_str(obj: BaseModel) -> str:
    """
    Convert a Pydantic BaseModel instance to a Markdown string.
    """
    md_str = f"## {obj.__class__.__name__}\n\n"
    for field, value in obj.dict().items():
        md_str += f"### {field}\n{value}\n\n"
    return md_str
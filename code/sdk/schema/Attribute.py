from pydantic import BaseModel


# TODO: redo this whole schema?
class Attribute(BaseModel):
    subject: str
    course_code: int
    attributes: dict[str, bool] # could use 'attributes' here but it bugs out
    
    def __init__(__pydantic_self__, **data: any) -> None:
        super().__init__(**data)

class Attributes(BaseModel):
    attributes:list[Attribute] = []
    
    def __init__(__pydantic_self__, **data: any) -> None:
        super().__init__(**data)
        
    def __repr__(self) -> str:
        return f"Attributes: {len(self.attributes)} courses."

    def __str__(self) -> str:
        return self.__repr__()
    
        
    def addAttrib(self,  attribute: Attribute):
        self.attributes.append(attribute) 
    
    def addAttribSkipDuplicates(self, attribute: Attribute):
        
        for c in self.attributes:
            if c.subject == attribute.subject and c.course_code == attribute.course_code:
                return None

        self.attributes.append(attribute)
        
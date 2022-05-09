import bson.errors
from pymongo import MongoClient
from typing import List, Dict, Union
from app.schemas.schema import Entity, Document,\
    DocumentCreateStructure, TemplateCreateStructure, Template
from bson.objectid import ObjectId
from fastapi import File, UploadFile
from app.models.parserwrapper import ParserWrapper


class Database:
    """
    A class for working with MongoDB database collections.
    """

    def __init__(self, uri: str):
        client = MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True)
        database = client['documentsAnalysis']
        self.documents = database['requirementsSpecifications']
        self.templates = database['sectionTreeTemplates']
        self.parser = ParserWrapper()

    def get_documents_short(self) -> Dict[str, List[Entity]]:
        """
        Returns short information about all documents in the database (ids and names).

        :return: dictionary containing :py:class:`DocumentShort` elements.
        """
        return self.__get_entities(self.documents)

    def get_documents(self) -> Dict[str, List[Document]]:
        """
        Returns information about all documents in the database (ids, names and structures).

        :return: a list of :py:class:`Document` elements.
        """
        documents: List[Document] = []
        for document in self.documents.find({}):
            documents.append(Document(
                id=str(document.get('_id')),
                name=document.get('name'),
                templateId=document.get('templateId'),
                structure=[document.get('structure')],
                keywords=[document.get('keywords')]
            ))
        return {'data': documents}

    def get_document(self, document_id: str) -> Union[Document, None]:
        """
        Returns information about the document from the resulting collection.
        """
        try:
            object_id = ObjectId(document_id)
        except bson.errors.InvalidId:
            return None

        document = self.documents.find_one({'_id': object_id})
        if document:
            return Document(
                id=str(document.get('_id')),
                name=document.get('name'),
                templateId=document.get('templateId'),
                structure=[document.get('structure')],
                keywords=[document.get('keywords')]
            )
        return None

    def get_mongo_documents(self) -> List[dict]:
        """
        Returns a list of objects stored in the resulting collection.
        """
        return list(self.documents.find({}))

    def update_document_structure(self, document_id: str, structure: List) -> str:
        """
        Updates information about a document that exists in the resulting collection.

        :param document_id: string representation of the document object id.
        :param structure: edited section structure.
        :return: status.
        """
        # we do not check the id for valid, since we first call the receiving method, which has a check
        document = {'_id': ObjectId(document_id)}
        new_data = {'$set': {'structure': structure[0]}}
        self.documents.update_one(document, new_data)
        return 'OK'

    def update_document_keywords(self, document_id: str, keywords: List):
        document = {'_id': ObjectId(document_id)}
        new_keywords = {'$set': {'keywords': keywords}}
        self.documents.update_one(document, new_keywords)
        return 'OK'

    def create_document(self, data: DocumentCreateStructure) -> bool:
        """
        Adds information about the new document to the resulting collection.

        :param data: class containing information about the document (name and structure).
        :return: returns True if the document was created successfully. Otherwise returns False.
        """
        try:
            template_id = ObjectId(data.templateId)
        except bson.errors.InvalidId:
            return False

        is_template_valid = self.templates.find_one({'_id': template_id})
        if not is_template_valid:
            return False

        is_structure_valid = self.parser.is_valid(data.structure[0])
        if not is_structure_valid:
            return False

        self.documents.insert_one({'name': data.name, 'templateId': data.templateId,
                                   'structure': data.structure[0], 'keywords': []})
        return True

    def delete_document(self, document_id: str) -> Union[str, None]:
        try:
            object_id = ObjectId(document_id)
        except bson.errors.InvalidId:
            return None

        self.documents.delete_one({'_id':  object_id})
        return 'OK'

    def get_templates_short(self) -> Dict[str, List[Entity]]:
        """
        Returns all structures templates for recognizing text documents.
        """
        return self.__get_entities(self.templates)

    def get_template(self, template_id: str) -> Union[Template, None]:
        """
        Returns information about the structure template from the collection with templates.
        """
        try:
            object_id = ObjectId(template_id)
        except bson.errors.InvalidId:
            return None

        template = self.templates.find_one({'_id': object_id})
        if template:
            return Template(
                id=str(template.get('_id')),
                name=template.get('name'),
                structure=[template.get('structure')]
            )
        return None

    def delete_template(self, template_id: str) -> Union[str, None]:
        try:
            object_id = ObjectId(template_id)
        except bson.errors.InvalidId:
            return None

        self.templates.delete_one({'_id':  object_id})
        return 'OK'

    def create_template(self, data: TemplateCreateStructure) -> bool:
        """
        Adds information about the new structure template to the collection with templates.

        :param data: class containing information about the structure template (name and structure).
        :return: returns True if the structure template was created successfully. Otherwise returns False.
        """
        is_structure_valid = self.parser.is_valid(data.structure)
        if not is_structure_valid:
            return False

        self.templates.insert_one({'name': data.name, 'structure': data.structure})
        return True

    async def parse_docx_by_template(self, template: Template, file: UploadFile = File(...)) -> list:
        """
        The wrapper method over method `parse_docx_by_template` from :py:class:`ParserWrapper`.
        """
        document_structure = await self.parser.parse_docx_by_template(template.structure[0], file)
        return [document_structure]

    @staticmethod
    def __get_entities(entity) -> Dict[str, List[Entity]]:
        entities: List[Entity] = []
        for value in entity.find({}):
            entities.append(Entity(
                id=str(value.get('_id')),
                name=value.get('name')
            ))
        return {'data': entities}

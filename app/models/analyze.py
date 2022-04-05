import os
from fastapi import File, UploadFile
from srsparser import SRSParser, NLProcessor
from typing import Any, List, Dict


class Analyze:

    def __init__(self):
        self.nlp = NLProcessor()

    @staticmethod
    def save_file(filename: str, data):
        with open(os.path.join('app', filename), 'wb') as f:
            f.write(data)

    async def parse_doc_by_template(self, template: Any, file: UploadFile = File(...)) -> dict:
        """
        :param file: Document
        :param template: Template
        :return: Method parse document
        """

        contents = await file.read()
        self.save_file(file.filename, contents)

        parser = SRSParser(template)
        document_structure = parser.parse_docx(f'./app/{file.filename}')

        os.remove(f'./app/{file.filename}')

        return document_structure

    def get_keywords_by_specification_id(self, specifications: List[Dict], doc_name: str, mode: str) -> List:
        """
        :param specifications: list of specifications
        :param doc_name: name of document
        :param mode: mode takes next variants: tf_idf, pullenti, combine
        :return: Method returns list of specification keywords
        """
        if mode == 'combine':
            return self.nlp.get_structure_keywords_with_ratios(specifications, doc_name)

        if mode == 'pullenti':
            return self.nlp.get_structure_keywords_pullenti(specifications, doc_name)

        if mode == 'tf_idf':
            return self.nlp.get_structure_keywords_tf_idf(specifications, doc_name)

        return []

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import ProcessPoolExecutor

from langchain.docstore.document import Document
from langchain.document_loaders import (
    PDFMinerLoader,
    Docx2txtLoader,
    TextLoader,
    JSONLoader,
    EverNoteLoader,
    UnstructuredEmailLoader,
    UnstructuredCSVLoader,
    UnstructuredExcelLoader
)

ROOT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
SOURCE_DIRECTORY = f"{ROOT_DIRECTORY}/Docs_for_DB"
INGEST_THREADS = os.cpu_count() or 8

DOCUMENT_MAP = {
    ".pdf": PDFMinerLoader,
    ".docx": Docx2txtLoader,
    ".txt": TextLoader,
    ".json": JSONLoader,
    ".enex": EverNoteLoader,
    ".eml": UnstructuredEmailLoader,
    ".msg": UnstructuredEmailLoader,
    ".csv": UnstructuredCSVLoader,
    ".xls": UnstructuredExcelLoader,
    ".xlsx": UnstructuredExcelLoader,
}

def load_single_document(file_path: str) -> Document:
    file_extension = os.path.splitext(file_path)[1]
    loader_class = DOCUMENT_MAP.get(file_extension)
    if loader_class:
        loader = loader_class(file_path)
    else:
        raise ValueError("Document type is undefined")
    return loader.load()[0]

def load_document_batch(filepaths):
    
    with ThreadPoolExecutor(len(filepaths)) as exe:
        futures = [exe.submit(load_single_document, name) for name in filepaths]
        data_list = [future.result() for future in futures]
    
    return (data_list, filepaths)

def load_documents(source_dir: str) -> list[Document]:
    
    all_files = os.listdir(source_dir)
    paths = [os.path.join(source_dir, file_path) for file_path in all_files if os.path.splitext(file_path)[1] in DOCUMENT_MAP.keys()]
    
    n_workers = min(INGEST_THREADS, max(len(paths), 1))
    chunksize = round(len(paths) / n_workers)
    docs = []
    
    with ProcessPoolExecutor(n_workers) as executor:
        futures = [executor.submit(load_document_batch, paths[i : (i + chunksize)]) for i in range(0, len(paths), chunksize)]
        for future in as_completed(futures):
            contents, _ = future.result()
            docs.extend(contents)
    
    return docs

if __name__ == "__main__":
    load_documents(SOURCE_DIRECTORY)

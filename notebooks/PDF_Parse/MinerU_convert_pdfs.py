## Convert pdfs to md and json 
#%%
import os
import argparse
import logging # Import logging
import fitz # Import PyMuPDF
import time # Import time
from pathlib import Path # Import Path
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod
from magic_pdf.data.batch_build_dataset import batch_build_dataset
from magic_pdf.tools.common import batch_do_parse
from tqdm import tqdm # Import tqdm

class PDFConverter:
    def __init__(self, input_dir, output_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir

    def process_pdf(self, pdf_file_path,pdf_output_dir=None,draw_pdf=False,verbose=False):
        # Create a unique directory for each PDF
        name_without_suffix = os.path.splitext(os.path.basename(pdf_file_path))[0]
        if pdf_output_dir is None:
            pdf_output_dir = os.path.join(self.output_dir, name_without_suffix)
        else:
            pdf_output_dir = os.path.join(pdf_output_dir, name_without_suffix)
        local_image_dir = os.path.join(pdf_output_dir, "images")
        local_md_dir = pdf_output_dir
        os.makedirs(local_image_dir, exist_ok=True)
        os.makedirs(local_md_dir, exist_ok=True)
        # read bytes
        image_writer = FileBasedDataWriter(local_image_dir)
        md_writer = FileBasedDataWriter(local_md_dir)
        # Readers
        reader = FileBasedDataReader("")
        pdf_bytes = reader.read(pdf_file_path)
        # Processing
        ds = PymuDocDataset(pdf_bytes)

        ## inference
        if ds.classify() == SupportedPdfParseMethod.OCR:
            infer_result = ds.apply(doc_analyze, ocr=True,show_log=verbose)
            pipe_result = infer_result.pipe_ocr_mode(image_writer)
        else:
            infer_result = ds.apply(doc_analyze, ocr=False,show_log=verbose)
            pipe_result = infer_result.pipe_txt_mode(image_writer)

        # Output
        if draw_pdf:
            infer_result.draw_model(os.path.join(local_md_dir, f"{name_without_suffix}_model.pdf"))
            pipe_result.draw_layout(os.path.join(local_md_dir, f"{name_without_suffix}_layout.pdf"))
            pipe_result.draw_span(os.path.join(local_md_dir, f"{name_without_suffix}_spans.pdf"))

        md_content = pipe_result.get_markdown(local_image_dir)
        pipe_result.dump_md(md_writer, f"{name_without_suffix}.md", local_image_dir)
        pipe_result.dump_content_list(md_writer, f"{name_without_suffix}_content_list.json", local_image_dir)
        pipe_result.dump_middle_json(md_writer, f"{name_without_suffix}_middle.json")

    def get_app_files(self, input_dir=None, endswith=".pdf", filter_invalid_pdf=False):
        """
        Collects file paths from the input directory matching the extension.
        Optionally filters out invalid PDF files.
        """
        if input_dir is None:
            input_dir = self.input_dir
        
        # Initial collection of all files matching the extension
        all_matching_files = []
        for root, dirs, files in os.walk(input_dir):
            for filename in files:
                if filename.lower().endswith(endswith):
                    all_matching_files.append(os.path.join(root, filename))

        # If filtering is requested, validate and filter
        if filter_invalid_pdf and endswith.lower() == ".pdf":
            logging.info("Filtering invalid PDFs during file collection...")
            valid_pdf_files = []
            # Use tqdm if filtering, as it might take time
            for pdf_file_path in tqdm(all_matching_files, desc="Validating PDFs"):
                if self.is_pdf_valid(pdf_file_path):
                    valid_pdf_files.append(pdf_file_path)
                else:
                    # Optionally log here as well, though is_pdf_valid already logs
                    logging.debug(f"Excluding invalid PDF: {pdf_file_path}") 
            logging.info(f"Found {len(valid_pdf_files)} valid PDF files after filtering.")
            return valid_pdf_files
        else:
            # Return all found files if no filtering is needed
            return all_matching_files
    
    def process_all_pdfs(self,input_dir=None,output_dir=None):
        if input_dir is None:
            input_dir = self.input_dir
        if output_dir is None:
            output_dir = self.output_dir
        # First collect all PDF files
        pdf_files = self.get_app_files(input_dir,endswith=".pdf")
       
        # Define error log file path
        error_log_path = os.path.join(output_dir, "error_log.txt")
       
        # Ensure the output directory exists for the log file
        os.makedirs(output_dir, exist_ok=True) 
       
        # Then process all collected PDF files with tqdm progress bar
        for pdf_file_path in tqdm(pdf_files, desc="Processing PDFs"):
            try:
                self.process_pdf(pdf_file_path, output_dir)
            except Exception as e:
                logging.error(f"Failed to process {pdf_file_path}: {e}", exc_info=True)
                # Append problematic PDF path to the error log file
                try:
                    with open(error_log_path, 'a') as error_file:
                        error_file.write(f"{pdf_file_path}\n")
                except Exception as log_e:
                    logging.error(f"Failed to write to error log {error_log_path}: {log_e}")
    
    def batch_process_pdfs(self,input_dir=None,output_dir=None,method="atuo",lang=""):
        if input_dir is None:
            input_dir = self.input_dir
        if output_dir is None:
            output_dir = self.output_dir
        
        pdf_files = self.get_app_files(input_dir,endswith=".pdf",filter_invalid_pdf=True)
        # build dataset with 2 workers
        datasets = batch_build_dataset(pdf_files, 4, lang)
        # os.environ["MINERU_MIN_BATCH_INFERENCE_SIZE"] = "200"  # every 200 pages will be parsed in one batch
        # Convert string paths to Path objects before accessing .stem
        batch_do_parse(output_dir, [Path(doc_path).stem for doc_path in pdf_files], datasets, method,
                       f_draw_span_bbox=False,
                       f_draw_layout_bbox=False,
                       f_dump_model_json=True,
                       f_dump_orig_pdf=False,
                       )

    def is_pdf_valid(self, pdf_file_path):
        """
        Performs a lightweight check to see if a PDF can be opened by PyMuPDF.
        Returns True if valid, False otherwise.
        """
        try:
            # Use a 'with' statement for automatic resource management
            with fitz.open(pdf_file_path) as doc:
                _ = doc.page_count  # Accessing page_count forces basic parsing
            return True
        except Exception as e:
            # Log the specific error encountered during validation
            logging.warning(f"Validation failed for {pdf_file_path}: {e}")
            return False

def parse_arguments(args_list=None):
    parser = argparse.ArgumentParser(description='Convert PDFs to Markdown and JSON format.')
    parser.add_argument('--input_dir', type=str, 
                        default="/ephemeral/home/xiong/data/Fund/pdf_parse/temp/input",
                        help='Directory containing input PDF files.')
    parser.add_argument('--output_dir', type=str, 
                        default="/ephemeral/home/xiong/data/Fund/pdf_parse/temp/output",
                        help='Directory where output files will be saved.')

    if args_list is not None:
        args = parser.parse_args(args_list) 
    else:
        args = parser.parse_args()    

    return args
#%%
if __name__ == "__main__":
    # Parse arguments
    args = parse_arguments([])
    os.makedirs(args.output_dir, exist_ok=True)
    converter = PDFConverter(input_dir=args.input_dir, 
                             output_dir=args.output_dir)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(os.path.join(args.output_dir, "processing.log")), # Log to a file in output dir
                            logging.StreamHandler() # Also log to console
                        ])
    # --- Time batch_process_pdfs ---
    logging.info("Starting batch_process_pdfs...")
    start_time_batch = time.time()
    converter.batch_process_pdfs(method="atuo",lang="en")
    end_time_batch = time.time()
    duration_batch = end_time_batch - start_time_batch
    logging.info(f"batch_process_pdfs completed in {duration_batch:.2f} seconds.")
    # -------------------------------
   
    # --- Time process_all_pdfs ---
    logging.info("Starting process_all_pdfs...")
    start_time_all = time.time()
    converter.process_all_pdfs()
    end_time_all = time.time()
    duration_all = end_time_all - start_time_all
    logging.info(f"process_all_pdfs completed in {duration_all:.2f} seconds.")
    # ----------------------------
    

# %%

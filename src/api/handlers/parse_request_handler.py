import os
import time
from queue import Queue
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import subprocess
import logging
import json

LOGGER = logging.getLogger(__name__)


class ParseRequestHandler:
    def __init__(self, number_of_workers=2):
        self.task_queue = Queue()
        self.worker_threads = []
        self.request_statuses = {}
        self.parsed_data = {}
        self.number_of_workers = number_of_workers

        for _ in range(self.number_of_workers):
            worker_thread = Thread(target=self.worker)
            worker_thread.daemon = True
            worker_thread.start()
            self.worker_threads.append(worker_thread)

    def handle_request(self, request_id, original_filename, image_bytes, pagination):
        renamed_filename = self.save_image_to_disk(
            pagination['page'], image_bytes, request_id)

        # Create a status object for the request
        request_status = {
            'total_pages': pagination['total'],
            'processed_pages': 0,
            'completed': False
        }
        self.request_statuses[request_id] = request_status

        self.task_queue.put((original_filename, renamed_filename, request_id))

        return {"success": "Image received and enqueued for processing"}, 200

    def save_image_to_disk(self, page, image_bytes, request_id):
        # Generate a unique file name for the image,
        # using user provided file name is a risk of collision and security issue
        timestamp = int(time.time() * 1000)
        renamed_filename = f"{request_id}_{timestamp}_{page}.jpg"

        # Save the image to a specific directory
        parse_directory = f"{os.path.dirname(os.path.dirname(__file__))}/receipt_parser/data/img"
        image_path = os.path.join(parse_directory, renamed_filename)
        with open(image_path, 'wb') as file:
            file.write(image_bytes)

        return renamed_filename

    def process_image(self, original_filename, renamed_filename, request_id):
        parsed_text_json = self.perform_ocr(renamed_filename)[0]
        parsed_text_json['file_name'] = original_filename

        if not isinstance(self.parsed_data.get(request_id), list):
            self.parsed_data[request_id] = []

        self.parsed_data[request_id].append(parsed_text_json)

        self.request_statuses[request_id]['processed_pages'] += 1

        # Check if all pages have been processed
        if self.request_statuses[request_id]['processed_pages'] == self.request_statuses[request_id]['total_pages']:
            self.request_statuses[request_id]['completed'] = True
            LOGGER.info(f"Request ID: {request_id} - All pages processed")

        # NOTE: Remove image file handled by parser
        # Therefore, we don't need to delete the image file here

    def perform_ocr(self, renamed_filename):
        def receipt_parser():
            """
            Thread function that runs the receipt parser as a subprocess and captures its output.
            The parser support multiple images in a single call, but we are only passing one image
            """

            try:
                subprocess_command = ["python3",
                                      "./src/api/receipt_parser/receipt_parser.py"]
                subprocess_command.append("1")
                subprocess_command.append(renamed_filename)

                parser_output_string = subprocess.check_output(
                    subprocess_command, encoding='utf-8')

                return parser_output_string

            except (OSError, subprocess.CalledProcessError) as exception:
                LOGGER.error('Exception occurred: ' + str(exception))
                return False

        with ThreadPoolExecutor() as executor:
            future = executor.submit(receipt_parser)
            return json.loads(future.result().splitlines()[-1])

    def worker(self):
        """
        Worker thread function that processes images in the queue
        """
        while True:
            original_filename, renamed_filename, request_id = self.task_queue.get()

            self.process_image(original_filename, renamed_filename, request_id)

            self.task_queue.task_done()

    # used by the Controller to check if all pages have been processed
    def is_all_pages_processed(self, request_id):
        return self.request_statuses[request_id]['completed']

    def get_parsed_data(self, request_id):
        return self.parsed_data[request_id]

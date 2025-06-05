import json
import argparse
import os

def convert_json_to_jsonl(input_file_path, output_file_path=None):
    """
    Converts a JSON file (containing a list of objects) to a JSONL file.

    In JSONL (JSON Lines) format, each line is a valid JSON object. This format 
    is commonly used for training machine learning models, especially large 
    language models, as it allows for efficient streaming and processing of large datasets.

    How this helps with training your custom legal language model:
    - Each JSON object on a line in the output .jsonl file preserves the 
      original structure from your input database (e.g., "nummer", "url", 
      "erscheinungsdatum", "gutachten_nummer", "rechtsbezug", and "text").
    - For fine-tuning a language model (like GPT or a Deepseek model) to understand 
      and generate legal text, the content of the "text" field within each JSON 
      object is typically the most crucial piece of data. The model will learn the 
      patterns, terminology, style, and information contained in these legal texts.
    - If your training pipeline expects a specific format (e.g., prompt/completion 
      pairs, or a single text field per JSON object), you might need to perform 
      further preprocessing on this generated JSONL file. For example:
        - For simple language modeling: You might extract just the "text" field, 
          so each line in a new file would be `{"text": "content of original text field..."}`.
        - For instruction fine-tuning: You could create pairs like 
          `{"instruction": "Analyze the following legal case:", "input": "<text field content>", "output": "<desired analysis if available>"}`
          or `{"prompt": "Relevant metadata...", "completion": "<text field content>"}`.
    - This script provides the foundational JSONL conversion. The exact structure 
      needed for fine-tuning can vary based on the specific model architecture and 
      training framework you use (e.g., Hugging Face, OpenAI API, custom PyTorch/TensorFlow code).
      Always consult the documentation for your chosen training platform.
    - The script attempts to handle JSON files that might have leading non-JSON lines 
      (like comments) before the main JSON array `[...]` starts, as seen in your example.
      However, the JSON content itself (within the array) must be valid.
    """
    if output_file_path is None:
        base, ext = os.path.splitext(input_file_path)
        output_file_path = base + ".jsonl"

    if input_file_path == output_file_path:
        print(f"Error: Input and potential output file paths would be the same (\'{input_file_path}').")
        print("If your input file already has a .jsonl extension, please rename it or ensure the script logic handles this.")
        return

    try:
        with open(input_file_path, 'r', encoding='utf-8') as infile:
            content = infile.read()
        
        # Attempt to find the start of the JSON array (e.g., '[')
        # This helps skip potential leading comments or non-JSON lines.
        array_start_index = content.find('[')
        object_start_index = content.find('{') # Fallback for a single object, though list is expected

        json_start_index = -1

        if array_start_index != -1 and (object_start_index == -1 or array_start_index < object_start_index):
            json_start_index = array_start_index
        elif object_start_index != -1:
            # This case is less likely for the user's described data (list of objects)
            # but makes the parser slightly more general if the input was a single JSON object file.
            # For this specific request, an array is expected.
            json_start_index = object_start_index 
            print("Warning: Input file seems to start with a JSON object '{' instead of an array '['. Processing as a single object list if parsing as array fails.")

        if json_start_index == -1:
            print("Error: Could not find the start of a JSON array ('[') or object ('{') in the input file.")
            print("Please ensure your file contains valid JSON data.")
            return

        json_content = content[json_start_index:]
        
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError as e:
            print(f"Error: Could not decode JSON from '{input_file_path}'. Details: {e}")
            print("Please ensure the content starting from the first '[' or '{' is valid JSON.")
            return

        if not isinstance(data, list):
            # If the top level is a single object, wrap it in a list to process consistently
            if isinstance(data, dict):
                data = [data]
            else:
                print("Error: Input JSON data is not a list of objects (or a single object).")
                return

        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            for entry in data:
                if not isinstance(entry, dict):
                    print(f"Warning: Skipping an item that is not a JSON object (dictionary): {type(entry)}")
                    continue
                # Serialize each entry (dictionary) to a JSON string
                # ensure_ascii=False is important for proper UTF-8 handling of special characters
                json_string = json.dumps(entry, ensure_ascii=False)
                outfile.write(json_string + '\n')
        
        print(f"Successfully converted '{input_file_path}' to '{output_file_path}'.")
        print(f"The output file contains {len(data)} lines, each being a JSON object.")

    except FileNotFoundError:
        print(f"Error: Input file '{input_file_path}' not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def convert_jsonl_to_json(input_file_path, output_file_path=None):
    """
    Converts a JSONL file (with one JSON object per line) to a JSON file containing a list of objects.
    
    JSONL (JSON Lines) files are often used for efficient processing of large datasets,
    especially in machine learning. This function converts such files back into a standard
    JSON array format, which might be easier to work with in some contexts.
    
    Args:
        input_file_path: Path to the input JSONL file
        output_file_path: Path to the output JSON file (optional). If not provided,
                          it will be derived from the input path by replacing the extension.
    """
    if output_file_path is None:
        base, ext = os.path.splitext(input_file_path)
        output_file_path = base + ".json"
    
    if input_file_path == output_file_path:
        print(f"Error: Input and potential output file paths would be the same (\'{input_file_path}').")
        print("If your input file already has a .json extension, please rename it or ensure the script logic handles this.")
        return
    
    try:
        data = []
        with open(input_file_path, 'r', encoding='utf-8') as infile:
            for line_number, line in enumerate(infile, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                try:
                    json_obj = json.loads(line)
                    data.append(json_obj)
                except json.JSONDecodeError as e:
                    print(f"Warning: Could not parse line {line_number} as JSON. Details: {e}")
                    print(f"Line content: {line[:50]}...")  # Show beginning of problematic line
                    print("This line will be skipped.")
        
        if not data:
            print("Warning: No valid JSON objects found in the input file.")
            return
        
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            json.dump(data, outfile, ensure_ascii=False, indent=2)
        
        print(f"Successfully converted '{input_file_path}' to '{output_file_path}'.")
        print(f"The output file contains a JSON array with {len(data)} objects.")
    
    except FileNotFoundError:
        print(f"Error: Input file '{input_file_path}' not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def detect_file_format(file_path):
    """
    Detect if a file is likely to be in JSON or JSONL format based on its content.
    
    Args:
        file_path: Path to the file to analyze
        
    Returns:
        A string indicating the detected format: 'json', 'jsonl', or 'unknown'
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_char = None
            # Find the first non-whitespace character
            while True:
                char = f.read(1)
                if not char:  # End of file
                    break
                if not char.isspace():  # Found a non-whitespace character
                    first_char = char
                    break
            
            if first_char is None:
                return 'unknown'  # Empty file
            
            if first_char == '[':
                # Likely a JSON file with array
                return 'json'
            elif first_char == '{':
                # Could be either a JSON object or a JSONL file starting with a JSON object
                # Read a bit more to check
                more_content = f.read(4000)  # Read a chunk to analyze
                if '\n{' in more_content:
                    return 'jsonl'  # Found another JSON object on a new line
                elif ']' in more_content and not '\n{' in more_content:
                    return 'json'  # Found closing bracket but no new JSON objects
                
                # Count the number of open and close braces to get a hint
                open_braces = more_content.count('{')
                close_braces = more_content.count('}')
                
                if open_braces > 1 and close_braces > 0 and '\n' in more_content:
                    return 'jsonl'  # Multiple objects likely means JSONL
                
                # Just look for new lines with JSON objects as a final check
                f.seek(0)
                lines = [line.strip() for line in f if line.strip()]
                if len(lines) > 1:
                    try:
                        # Try to parse the second line as JSON
                        if lines[1].startswith('{') and lines[1].endswith('}'):
                            json.loads(lines[1])
                            return 'jsonl'  # Second line is a valid JSON object
                    except (json.JSONDecodeError, IndexError):
                        pass
                
                return 'json'  # Default to JSON if unsure
            
            return 'unknown'  # Unrecognized format
    
    except Exception as e:
        print(f"Error detecting file format: {e}")
        return 'unknown'


def main(input_file_path, output_file_path=None, conversion_type=None):
    """
    Main function to handle file conversion between JSON and JSONL formats.
    
    Args:
        input_file_path: Path to the input file
        output_file_path: Path to the output file (optional)
        conversion_type: 'to_jsonl', 'to_json', or None for auto-detection
    """
    # Validate input file exists
    if not os.path.isfile(input_file_path):
        print(f"Error: Input file '{input_file_path}' not found.")
        return
    
    # Auto-detect conversion type if not specified
    if conversion_type is None:
        file_format = detect_file_format(input_file_path)
        if file_format == 'json':
            conversion_type = 'to_jsonl'
        elif file_format == 'jsonl':
            conversion_type = 'to_json'
        else:
            print(f"Error: Could not detect the format of '{input_file_path}'.")
            print("Please specify the conversion direction explicitly using --to-jsonl or --to-json.")
            return
    
    # Execute the appropriate conversion
    if conversion_type == 'to_jsonl':
        convert_json_to_jsonl(input_file_path, output_file_path)
    elif conversion_type == 'to_json':
        convert_jsonl_to_json(input_file_path, output_file_path)
    else:
        print(f"Error: Unknown conversion type '{conversion_type}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert between JSON and JSONL formats.\n"+
                    "The JSONL format has one JSON object per line, while JSON format has a list of objects.\n"+
                    "Example: python jsonl_converter.py your_data.json\n"+
                    "Example: python jsonl_converter.py your_data.jsonl --to-json",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_file_path",
        type=str,
        help="Path to the input file (either JSON or JSONL format)."
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Path to the output file. If not specified, it will be derived from the input path.",
        dest="output_file_path"
    )
    
    # Conversion direction options
    direction_group = parser.add_mutually_exclusive_group()
    direction_group.add_argument(
        "--to-jsonl",
        action="store_const",
        const="to_jsonl",
        dest="conversion_type",
        help="Convert from JSON to JSONL format."
    )
    direction_group.add_argument(
        "--to-json",
        action="store_const",
        const="to_json",
        dest="conversion_type",
        help="Convert from JSONL to JSON format."
    )

    args = parser.parse_args()

    main(args.input_file_path, args.output_file_path, args.conversion_type)

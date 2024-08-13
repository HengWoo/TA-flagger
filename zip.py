import shutil

def zip_folder(folder_path, output_path):
    shutil.make_archive(output_path, 'zip', folder_path)

# Example usage
folder_path = '/cloudide/workspace/sugar-quant/TA-flagger'
output_path = '/cloudide/workspace/sugar-quant/TA-flagger/zip_TA-flagger'
zip_folder(folder_path, output_path)